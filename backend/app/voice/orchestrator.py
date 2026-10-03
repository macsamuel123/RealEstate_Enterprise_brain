"""Voice orchestrator - ties together STT, dispatch, TTS for voice interaction."""
from typing import Optional, Dict, Any, AsyncGenerator
from uuid import UUID
import logging
import asyncio
from datetime import datetime

from app.voice.stt import WhisperSTT, AudioFormat
from app.voice.tts import ElevenLabsTTS, VoiceID
from app.agents.dispatch import OrchestratorDispatch, TaskEnvelope
from app.database import get_supabase
from app.models import ConversationChannel

logger = logging.getLogger(__name__)


class VoiceOrchestrator:
    """
    Handle complete voice interaction flow:

    1. User speaks (audio bytes arrive)
    2. STT (Whisper) converts to text
    3. Dispatch (agents) processes the text
    4. TTS (ElevenLabs) converts response to audio
    5. Audio streams to user
    """

    def __init__(
        self,
        org_id: UUID,
        user_id: UUID,
        whisper_api_key: str,
        elevenlabs_api_key: str,
        voice_id: str = VoiceID.ADAM
    ):
        self.org_id = org_id
        self.user_id = user_id
        self.supabase = get_supabase()

        # Initialize pipelines
        self.stt = WhisperSTT(api_key=whisper_api_key)
        self.tts = ElevenLabsTTS(
            api_key=elevenlabs_api_key,
            voice_id=voice_id
        )
        self.dispatch = OrchestratorDispatch(org_id, user_id)

    async def handle_voice_message(
        self,
        audio_data: bytes,
        audio_format: AudioFormat = AudioFormat.WAV,
        conversation_id: Optional[UUID] = None,
        user_context: Optional[str] = None  # Pre-call briefing
    ) -> Dict[str, Any]:
        """
        Handle a complete voice interaction.

        Args:
            audio_data: Raw audio bytes from user
            audio_format: Format of audio (WAV, MP3, etc)
            conversation_id: Existing conversation or create new
            user_context: Pre-call briefing to improve understanding

        Returns: {
            "status": "success",
            "transcript": "what user said",
            "response": "what agent said",
            "audio": bytes,
            "duration": 2.5,
            "conversation_id": uuid
        }
        """

        try:
            # Create conversation if needed
            if not conversation_id:
                conv = self.supabase.table("conversation").insert({
                    "org_id": str(self.org_id),
                    "user_id": str(self.user_id),
                    "channel": ConversationChannel.VOICE.value,
                    "title": f"Voice call - {datetime.utcnow().isoformat()}"
                }).execute()
                conversation_id = conv.data[0]["id"]

            # Step 1: STT - Convert audio to text
            logger.info(f"STT: Processing {len(audio_data)} bytes of audio...")
            stt_result = await self.stt.transcribe(
                audio_data=audio_data,
                audio_format=audio_format,
                prompt=user_context  # Use pre-call briefing as prompt
            )
            transcript = stt_result["text"]
            logger.info(f"STT: '{transcript}'")

            # Step 2: Dispatch - Process user message
            logger.info(f"Dispatch: Routing '{transcript}'...")
            dispatch_result = await self.dispatch.handle_user_message(
                message=transcript,
                conversation_id=conversation_id
            )
            response_text = dispatch_result.get("response", "I'm not sure what you're asking for.")
            logger.info(f"Dispatch: Response generated ({len(response_text)} chars)")

            # Step 3: TTS - Convert response to audio
            # Use Haiku (fast) for live calls to minimize latency
            logger.info(f"TTS: Synthesizing response...")
            tts_result = await self.tts.synthesize(
                text=response_text,
                stability=0.5,  # More natural variation for voice
                similarity_boost=0.75
            )
            response_audio = tts_result["audio"]
            logger.info(f"TTS: Generated {len(response_audio)} bytes ({tts_result['duration']:.1f}s)")

            # Step 4: Store conversation
            self.supabase.table("message").insert({
                "org_id": str(self.org_id),
                "conversation_id": str(conversation_id),
                "role": "user",
                "content": transcript
            }).execute()

            self.supabase.table("message").insert({
                "org_id": str(self.org_id),
                "conversation_id": str(conversation_id),
                "role": "assistant",
                "content": response_text
            }).execute()

            return {
                "status": "success",
                "transcript": transcript,
                "response": response_text,
                "audio": response_audio,
                "duration": tts_result["duration"],
                "conversation_id": str(conversation_id),
                "delegations": dispatch_result.get("delegations", [])
            }

        except Exception as e:
            logger.error(f"Voice orchestration failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "conversation_id": str(conversation_id) if conversation_id else None
            }

    async def stream_voice_message(
        self,
        audio_stream,  # AsyncGenerator yielding audio chunks
        conversation_id: Optional[UUID] = None,
        user_context: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Handle streaming voice (real-time conversation).

        Flow:
        1. Buffer audio chunks (wait for silence or timeout)
        2. STT on buffer
        3. Dispatch
        4. Stream TTS audio to user as it generates

        Yields: {
            "type": "transcript" | "response_chunk" | "complete",
            "data": str | bytes | dict
        }
        """

        try:
            # Create conversation
            if not conversation_id:
                conv = self.supabase.table("conversation").insert({
                    "org_id": str(self.org_id),
                    "user_id": str(self.user_id),
                    "channel": ConversationChannel.VOICE.value,
                    "title": f"Voice stream - {datetime.utcnow().isoformat()}"
                }).execute()
                conversation_id = conv.data[0]["id"]

            # Buffer audio until silence detected or timeout
            audio_buffer = b""
            silence_threshold = 0.5  # seconds of silence = end of speech
            last_audio_time = datetime.utcnow()

            async for chunk in audio_stream:
                audio_buffer += chunk
                last_audio_time = datetime.utcnow()

                # Check for silence timeout
                elapsed = (datetime.utcnow() - last_audio_time).total_seconds()
                if elapsed > silence_threshold and audio_buffer:
                    # Process buffered audio
                    break

            # Step 1: STT
            stt_result = await self.stt.transcribe(
                audio_data=audio_buffer,
                prompt=user_context
            )
            transcript = stt_result["text"]

            yield {
                "type": "transcript",
                "data": transcript
            }

            # Step 2: Dispatch
            dispatch_result = await self.dispatch.handle_user_message(
                message=transcript,
                conversation_id=conversation_id
            )
            response_text = dispatch_result.get("response", "")

            # Step 3: Stream TTS
            async for audio_chunk in self.tts.stream_synthesize(response_text):
                yield {
                    "type": "response_chunk",
                    "data": audio_chunk
                }

            # Step 4: Final result
            yield {
                "type": "complete",
                "data": {
                    "transcript": transcript,
                    "response": response_text,
                    "conversation_id": str(conversation_id),
                    "delegations": dispatch_result.get("delegations", [])
                }
            }

        except Exception as e:
            logger.error(f"Streaming voice failed: {e}", exc_info=True)
            yield {
                "type": "error",
                "data": str(e)
            }

    async def get_pre_call_briefing(self, contact_id: Optional[UUID] = None) -> str:
        """
        Get context before an inbound call (pre-call briefing).

        Returns: Briefing text to pass as prompt to STT/Dispatch
        """

        if not contact_id:
            return ""

        try:
            # Get contact info
            contact = self.supabase.table("contact").select("*").eq(
                "id", str(contact_id)
            ).single().execute()

            contact_data = contact.data or {}

            # Search memory for relevant facts
            from app.tools.handlers import ToolHandlers
            handlers = ToolHandlers(self.supabase)

            memory_result = await handlers.memory_search(
                org_id=self.org_id,
                user_id=self.user_id,
                query=f"calls with {contact_data.get('name', 'this person')}",
                limit=3
            )

            memories = memory_result.get("memories", [])

            # Build briefing
            briefing_parts = [
                f"Incoming call from {contact_data.get('name', 'Unknown')}",
                f"Email: {contact_data.get('email', 'Not on file')}",
                f"Phone: {contact_data.get('phone', 'Not on file')}",
                f"Company: {contact_data.get('company', 'Unknown')}",
            ]

            if memories:
                briefing_parts.append("\nRecent context:")
                for mem in memories:
                    briefing_parts.append(f"- {mem.get('fact', '')}")

            return "\n".join(briefing_parts)

        except Exception as e:
            logger.warning(f"Failed to get pre-call briefing: {e}")
            return ""
