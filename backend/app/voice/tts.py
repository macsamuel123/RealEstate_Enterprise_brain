"""Text-to-Speech pipeline using ElevenLabs API."""
from typing import Optional, Dict, Any, AsyncGenerator
import logging
import io
from enum import Enum

logger = logging.getLogger(__name__)


class VoiceID(str, Enum):
    """ElevenLabs voice IDs - Jarvis-style profiles."""
    ADAM = "pNInz6obpgDQGcFmaJgO"        # Deep, authoritative
    BELLA = "EXAVITQu4vr4xnSDxMaL"      # Professional female
    CALLUM = "N2lVS1Hs4NCs3DIPqeCl"     # British male
    CHARLIE = "IZe4tHaLKqnVsxEUcNXT"    # Confident, energetic
    ELLY = "MF3mGyEYCl7XYWbV7V2Z"       # Warm, friendly
    GIGI = "jBpfuIE2acCO8z3wKNLl"       # Youthful, spirited


class ElevenLabsTTS:
    """Text-to-Speech using ElevenLabs API."""

    def __init__(self, api_key: str, voice_id: str = VoiceID.ADAM):
        self.api_key = api_key
        self.voice_id = voice_id
        self.base_url = "https://api.elevenlabs.io/v1"

    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> Dict[str, Any]:
        """
        Convert text to speech.

        Args:
            text: Text to synthesize
            voice_id: ElevenLabs voice ID (default: self.voice_id)
            stability: 0-1, lower = more variable emotion
            similarity_boost: 0-1, higher = more consistent with voice

        Returns: {
            "audio": bytes,
            "duration": 2.5,
            "character_count": 42,
            "characters_remaining": 199958
        }
        """

        try:
            import httpx

            voice_id = voice_id or self.voice_id

            url = f"{self.base_url}/text-to-speech/{voice_id}"

            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()

                audio_data = response.content

                # Estimate duration (rough: ~150 chars per second)
                estimated_duration = len(text) / 150

                result = {
                    "audio": audio_data,
                    "duration": estimated_duration,
                    "character_count": len(text),
                    "characters_remaining": response.headers.get("x-characters-remaining", 0)
                }

                logger.info(f"Synthesized {len(text)} chars → {len(audio_data)} bytes ({estimated_duration:.1f}s)")
                return result

        except Exception as e:
            logger.error(f"ElevenLabs synthesis failed: {e}")
            raise

    async def stream_synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream audio chunks as they're generated.

        Useful for real-time voice: start playing audio while still generating.
        Yields: audio_chunk (bytes)
        """

        try:
            import httpx

            voice_id = voice_id or self.voice_id

            url = f"{self.base_url}/text-to-speech/{voice_id}/stream"

            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost
                }
            }

            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    url,
                    json=payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()

                    async for chunk in response.aiter_bytes(chunk_size=4096):
                        if chunk:
                            yield chunk

        except Exception as e:
            logger.error(f"ElevenLabs streaming synthesis failed: {e}")
            raise


class LocalTTS:
    """
    Fallback: Text-to-Speech using local models (gTTS, pyttsx3, etc).

    Fallback chain:
    1. ElevenLabs API (best quality)
    2. gTTS (Google Text-to-Speech, free)
    3. pyttsx3 (offline, lower quality)
    """

    @staticmethod
    async def gtts_synthesize(text: str) -> Dict[str, Any]:
        """Synthesize using Google Text-to-Speech (free, lower quality)."""

        try:
            from gtts import gTTS

            tts = gTTS(text=text, lang='en', slow=False)

            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_data = audio_buffer.getvalue()

            estimated_duration = len(text) / 150

            return {
                "audio": audio_data,
                "duration": estimated_duration,
                "character_count": len(text),
                "method": "gTTS"
            }

        except ImportError:
            raise ImportError("gTTS requires: pip install gtts")
        except Exception as e:
            logger.error(f"gTTS synthesis failed: {e}")
            raise

    @staticmethod
    async def pyttsx3_synthesize(text: str) -> Dict[str, Any]:
        """Synthesize using pyttsx3 (offline, but lower quality)."""

        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty('rate', 150)  # Speed
            engine.setProperty('volume', 0.9)

            # Save to bytes buffer
            audio_buffer = io.BytesIO()
            engine.save_to_file(text, '/tmp/temp_audio.wav')
            engine.runAndWait()

            with open('/tmp/temp_audio.wav', 'rb') as f:
                audio_data = f.read()

            estimated_duration = len(text) / 150

            return {
                "audio": audio_data,
                "duration": estimated_duration,
                "character_count": len(text),
                "method": "pyttsx3"
            }

        except ImportError:
            raise ImportError("pyttsx3 requires: pip install pyttsx3")
        except Exception as e:
            logger.error(f"pyttsx3 synthesis failed: {e}")
            raise
