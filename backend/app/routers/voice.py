"""Voice API endpoints - REST + WebSocket for voice interaction."""
from fastapi import APIRouter, UploadFile, File, WebSocket, Depends, HTTPException
from fastapi.responses import StreamingResponse
from uuid import UUID
import logging
import os
from typing import Optional
from pydantic import BaseModel

from app.voice.orchestrator import VoiceOrchestrator
from app.voice.stt import AudioFormat
from app.agents.claude_agent import chat as claude_chat
from app.config import settings
from uuid import uuid4

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["voice", "agent"])


class AgentRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None


class TTSRequest(BaseModel):
    text: str
    voice_id: str = None
    model: str = "eleven_monolingual_v1"
    speed: float = 1.0


@router.post("/message")
async def voice_message(
    audio: UploadFile = File(...),
    conversation_id: str = None
):
    """
    Send a voice message (audio file) and get response.

    Args:
        audio: Audio file (WAV, MP3, etc)
        conversation_id: Optional existing conversation

    Returns:
        {
            "transcript": "what user said",
            "response": "what agent said",
            "audio_url": "URL to download response audio",
            "conversation_id": "uuid"
        }
    """

    try:
        org_id = current_user.org_id
        user_id = current_user.id

        # Read audio
        audio_data = await audio.read()

        # Detect format from filename
        audio_format = AudioFormat.WAV
        if audio.filename:
            ext = audio.filename.split(".")[-1].lower()
            try:
                audio_format = AudioFormat(ext)
            except ValueError:
                audio_format = AudioFormat.WAV

        # Initialize orchestrator
        voice_orch = VoiceOrchestrator(
            org_id=org_id,
            user_id=user_id,
            whisper_api_key=os.getenv("OPENAI_API_KEY"),
            elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY")
        )

        # Parse conversation_id if provided
        conv_id = None
        if conversation_id:
            try:
                conv_id = UUID(conversation_id)
            except ValueError:
                pass

        # Get pre-call briefing (for context)
        briefing = await voice_orch.get_pre_call_briefing()

        # Process voice
        result = await voice_orch.handle_voice_message(
            audio_data=audio_data,
            audio_format=audio_format,
            conversation_id=conv_id,
            user_context=briefing
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])

        # TODO: Store audio file and return signed URL
        # For now, return audio inline (small files only)

        return {
            "transcript": result["transcript"],
            "response": result["response"],
            "conversation_id": result["conversation_id"],
            "duration": result["duration"],
            "delegations": result["delegations"]
        }

    except Exception as e:
        logger.error(f"Voice message failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/stream")
async def voice_stream(websocket: WebSocket, conversation_id: str = None):
    """
    WebSocket for streaming voice (real-time conversation).

    Client sends: {
        "type": "audio_chunk" | "control",
        "data": bytes | dict
    }

    Server sends: {
        "type": "transcript" | "response_chunk" | "complete" | "error",
        "data": str | bytes | dict
    }
    """

    await websocket.accept()

    try:
        # TODO: Extract org_id, user_id from WebSocket auth
        # For now, stub
        org_id = None
        user_id = None

        if not org_id or not user_id:
            await websocket.send_json({
                "type": "error",
                "data": "Authentication required"
            })
            await websocket.close(code=1008)
            return

        # Initialize orchestrator
        voice_orch = VoiceOrchestrator(
            org_id=org_id,
            user_id=user_id,
            whisper_api_key=os.getenv("OPENAI_API_KEY"),
            elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY")
        )

        # Parse conversation_id if provided
        conv_id = None
        if conversation_id:
            try:
                conv_id = UUID(conversation_id)
            except ValueError:
                pass

        async def audio_stream_generator():
            """Receive audio chunks from WebSocket client."""
            while True:
                try:
                    message = await websocket.receive_json()

                    if message.get("type") == "audio_chunk":
                        # Convert base64 to bytes
                        import base64
                        audio_bytes = base64.b64decode(message.get("data", ""))
                        yield audio_bytes

                    elif message.get("type") == "control":
                        # Handle control messages (end stream, etc)
                        if message.get("action") == "end":
                            break

                except Exception as e:
                    logger.error(f"Error receiving audio chunk: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "data": str(e)
                    })
                    break

        # Get pre-call briefing
        briefing = await voice_orch.get_pre_call_briefing()

        # Process streaming voice
        async for response in voice_orch.stream_voice_message(
            audio_stream=audio_stream_generator(),
            conversation_id=conv_id,
            user_context=briefing
        ):
            if response["type"] == "response_chunk":
                # Send audio chunk as base64
                import base64
                audio_b64 = base64.b64encode(response["data"]).decode()
                await websocket.send_json({
                    "type": "response_chunk",
                    "data": audio_b64
                })
            else:
                # Send other messages as-is
                await websocket.send_json(response)

    except Exception as e:
        logger.error(f"WebSocket voice stream error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "data": str(e)
            })
        except:
            pass
        await websocket.close(code=1011)


@router.get("/briefing/{contact_id}")
async def get_call_briefing(
    contact_id: UUID
):
    """
    Get pre-call briefing for an inbound call.

    Returns:
        {
            "name": "John Smith",
            "context": "briefing text",
            "recent_deals": [...],
            "memory": [...]
        }
    """

    try:
        org_id = "org_getty_group"  # Mock for testing
        user_id = "user_shawn_getty"  # Mock for testing

        voice_orch = VoiceOrchestrator(
            org_id=org_id,
            user_id=user_id,
            whisper_api_key=os.getenv("OPENAI_API_KEY"),
            elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY")
        )

        briefing = await voice_orch.get_pre_call_briefing(contact_id=contact_id)

        return {
            "contact_id": str(contact_id),
            "briefing": briefing
        }

    except Exception as e:
        logger.error(f"Failed to get call briefing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...)
):
    """Transcribe audio to text via Whisper."""
    try:
        if not audio.file:
            raise HTTPException(400, "No audio file provided")

        audio_data = await audio.read()
        openai_key = os.getenv("OPENAI_API_KEY")

        if not openai_key:
            raise HTTPException(401, "OpenAI API key not configured")

        # Call OpenAI Whisper API
        import httpx

        files = {
            "file": ("audio.webm", audio_data, "audio/webm"),
            "model": (None, "whisper-1"),
        }

        headers = {"Authorization": f"Bearer {openai_key}"}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers=headers,
                files=files,
            )

            if resp.status_code != 200:
                logger.error(f"Whisper error: {resp.text}")
                raise HTTPException(resp.status_code, "Transcription failed")

            data = resp.json()
            return {"text": data.get("text", "")}

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(500, str(e))


# In-memory conversation store (for demo; move to Supabase later)
_conversations = {}


@router.post("/agent")
async def agent(req: AgentRequest):
    """Process question through Claude agent."""
    try:
        logger.info(f"[AGENT] Question: '{req.question}'")

        if not req.question.strip():
            raise HTTPException(400, "Question cannot be empty")

        org_id = "org_getty_group"
        user_id = "user_shawn_getty"

        # Get or create conversation
        conv_id = req.conversation_id or str(uuid4())
        history = _conversations.get(conv_id, [])

        logger.info(f"[AGENT] Using conversation_id={conv_id}, history length={len(history)}")

        # Call Claude agent
        response_text, updated_history, pending_approval = await claude_chat(
            user_message=req.question,
            conversation_history=history,
            org_id=org_id,
            user_id=user_id
        )

        # Store updated history
        _conversations[conv_id] = updated_history

        logger.info(f"[AGENT] Response: '{response_text}'")

        result = {
            "response": response_text,
            "conversation_id": conv_id
        }

        if pending_approval:
            result["pending_approval"] = pending_approval

        return result

    except Exception as e:
        logger.error(f"[AGENT ERROR] {e}", exc_info=True)
        raise HTTPException(500, str(e))


@router.post("/tts")
async def text_to_speech(
    req: TTSRequest
):
    """Convert text to speech via ElevenLabs."""
    try:
        api_key = settings.elevenlabs_api_key
        if not api_key:
            raise HTTPException(401, "ElevenLabs API key not configured")

        voice_id = req.voice_id or settings.elevenlabs_voice_id

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        payload = {
            "text": req.text,
            "model_id": req.model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            }
        }

        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }

        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers)

            if resp.status_code != 200:
                logger.error(f"ElevenLabs error: {resp.text}")
                raise HTTPException(resp.status_code, "TTS failed")

            return StreamingResponse(
                iter([resp.content]),
                media_type="audio/mpeg"
            )

    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(500, str(e))


import os
