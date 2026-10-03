"""Speech-to-Text pipeline using OpenAI Whisper."""
from typing import Optional, Dict, Any
import logging
import io
from enum import Enum

from openai import OpenAI

logger = logging.getLogger(__name__)


class AudioFormat(str, Enum):
    """Supported audio formats for Whisper."""
    MP3 = "mp3"
    MP4 = "mp4"
    MPEG = "mpeg"
    MPGA = "mpga"
    M4A = "m4a"
    WAV = "wav"
    WEBM = "webm"


class WhisperSTT:
    """Speech-to-Text using OpenAI Whisper API."""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "whisper-1"

    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: AudioFormat = AudioFormat.WAV,
        language: str = "en",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text.

        Args:
            audio_data: Raw audio bytes
            audio_format: Format of audio
            language: Language code (en, es, fr, etc)
            prompt: Optional context for transcription (improves accuracy)

        Returns: {
            "text": "transcribed text",
            "duration": 2.5,
            "language": "en",
            "confidence": 0.95
        }
        """

        try:
            # Convert bytes to file-like object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{audio_format.value}"

            # Call Whisper API
            transcript = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language,
                prompt=prompt,
                response_format="verbose_json"  # Get detailed response
            )

            result = {
                "text": transcript.text,
                "duration": transcript.duration if hasattr(transcript, 'duration') else None,
                "language": language,
                "confidence": transcript.confidence if hasattr(transcript, 'confidence') else 0.9
            }

            logger.info(f"Transcribed {len(audio_data)} bytes → {len(transcript.text)} chars")
            return result

        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise

    async def stream_transcribe(
        self,
        audio_stream,
        language: str = "en",
        prompt: Optional[str] = None
    ):
        """
        Transcribe streaming audio chunks in real-time.

        For live calls, chunk audio as it arrives and transcribe incrementally.
        Yields: {"text": "partial transcription", "is_final": False/True}
        """

        # TODO: Implement streaming transcription via WebSocket
        # For now, buffer and transcribe at the end

        audio_buffer = b""
        async for chunk in audio_stream:
            audio_buffer += chunk

        result = await self.transcribe(
            audio_data=audio_buffer,
            language=language,
            prompt=prompt
        )

        yield {
            "text": result["text"],
            "is_final": True,
            "duration": result["duration"]
        }


class LocalWhisperSTT:
    """
    Fallback: Run Whisper locally (for offline use or privacy).
    Requires: pip install openai-whisper

    Note: Much slower than API (real-time factor ~3-5x vs API ~0.5x)
    """

    def __init__(self):
        try:
            import whisper
            self.whisper = whisper
            self.model = whisper.load_model("base")
        except ImportError:
            raise ImportError("Local Whisper requires: pip install openai-whisper")

    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: AudioFormat = AudioFormat.WAV,
        language: str = "en",
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe using local Whisper model."""

        try:
            # Save to temp file (whisper requires file path)
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=f".{audio_format.value}", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            # Transcribe
            result = self.model.transcribe(
                tmp_path,
                language=language,
                initial_prompt=prompt
            )

            return {
                "text": result["text"],
                "duration": None,
                "language": language,
                "confidence": 0.9  # Local model doesn't return confidence
            }

        except Exception as e:
            logger.error(f"Local Whisper transcription failed: {e}")
            raise
