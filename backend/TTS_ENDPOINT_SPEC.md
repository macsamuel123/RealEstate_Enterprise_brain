# Voice Integration Endpoints

For the voice-first ring interface to work, the backend needs three endpoints:
1. **STT** (`POST /api/transcribe`) — Speech-to-Text
2. **Agent** (`POST /api/agent`) — Process question, return answer
3. **TTS** (`POST /api/tts`) — Text-to-Speech

## Voice Flow

```
User speaks → STT (Whisper) → Question text
           ↓
        Agent processes (routes to agents, generates answer)
           ↓
        Answer text → TTS (ElevenLabs) → Play audio
```

---

## Endpoint 1: STT (Speech-to-Text)

```
POST /api/transcribe
```

### Request

Multipart form data:
- `audio` (file) — WebM audio blob from MediaRecorder

### Response

**200 OK**
```json
{
  "text": "What are my new leads today?"
}
```

**400 Bad Request**
- Audio file is empty or missing

**500 Internal Server Error**
- Whisper API call failed

### Backend Implementation (Python/FastAPI)

```python
from fastapi import APIRouter, UploadFile, File, HTTPException
import httpx
import os

router = APIRouter()

@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Transcribe audio to text via OpenAI Whisper"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(401, "OpenAI API key not configured")
    
    if not audio.file:
        raise HTTPException(400, "No audio file provided")
    
    # Read audio buffer
    audio_data = await audio.read()
    
    # Call OpenAI Whisper API
    files = {
        'file': ('audio.webm', audio_data, 'audio/webm'),
        'model': (None, 'whisper-1'),
    }
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers,
            files=files,
        )
        
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"Whisper error: {resp.text}")
        
        data = resp.json()
        return {"text": data.get("text", "")}
```

---

## Endpoint 2: Agent (Process Question, Return Answer)

```
POST /api/agent
```

### Request

```json
{
  "question": "What are my new leads today?"
}
```

### Response

**200 OK**
```json
{
  "response": "You have 7 new leads today. The Chen family is ready to view 123 Aspen Ridge Drive..."
}
```

**400 Bad Request**
- Question is empty

**500 Internal Server Error**
- Agent processing failed

### Backend Implementation (Python/FastAPI)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class AgentRequest(BaseModel):
    question: str

@router.post("/agent")
async def agent_endpoint(req: AgentRequest):
    """Process question through orchestrator, return agent response"""
    
    if not req.question.strip():
        raise HTTPException(400, "Question cannot be empty")
    
    # Route through orchestrator (from Layer 4)
    from app.agents.orchestrator import Orchestrator
    
    orchestrator = Orchestrator()
    
    try:
        response = await orchestrator.process(req.question)
        return {"response": response}
    except Exception as e:
        raise HTTPException(500, f"Agent error: {str(e)}")
```

---

## Endpoint 3: TTS (Text-to-Speech)

```
POST /api/tts
```

## Request

```json
{
  "text": "You have 7 new leads today",
  "voice_id": "string (optional, defaults to env ELEVENLABS_VOICE_ID)",
  "model": "string (optional, defaults to 'eleven_monolingual_v1')",
  "speed": "number (optional, 0.5-2.0, defaults to 1.0)"
}
```

## Response

**200 OK**
- Content-Type: `audio/mpeg` (MP3 audio buffer)
- Body: Raw audio bytes ready for Web Audio API decoding

**400 Bad Request**
- Text is empty or missing

**401 Unauthorized**
- ELEVENLABS_API_KEY not set

**500 Internal Server Error**
- ElevenLabs API call failed

## Backend Implementation (Python/FastAPI)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    voice_id: str = None
    model: str = "eleven_monolingual_v1"
    speed: float = 1.0

@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    """Convert text to speech via ElevenLabs"""
    
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(401, "ElevenLabs API key not configured")
    
    voice_id = req.voice_id or os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    
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
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        
        if resp.status_code != 200:
            raise HTTPException(resp.status_code, f"ElevenLabs error: {resp.text}")
        
        return StreamingResponse(
            iter([resp.content]),
            media_type="audio/mpeg"
        )
```

## Frontend Usage

The frontend calls this endpoint automatically via `src/services/tts.ts`:

```typescript
import { speak } from '@/services/tts';

// When agent responds:
await speak("You have 7 new leads today");
// → Calls POST /api/tts → decodes audio → plays via Web Audio API
```

## ElevenLabs Voice IDs

Popular voices for AI assistant tone:
- `21m00Tcm4TlvDq8ikWAM` — Default (neutral, professional)
- `EXAVITQu4vr4xnSDxMaL` — Bella (warm, engaging)
- `TxGEqnHWrfWFTfGW9XjX` — Antoni (deep, authoritative)
- `VR6AewLbuHnvgcsw1xZY` — Arnold (robotic, tech-like)

Set `ELEVENLABS_VOICE_ID` in `.env` to pick one.

## Latency Target

- Goal: <500ms round-trip for speech to start playing (acceptable for voice interaction)
- ElevenLabs typical: 200-400ms for short text
- Network + decode: ~100ms
- **Total: ~300-500ms** ✓

## Rate Limits

ElevenLabs free tier: 10,000 characters/month (~20 briefs)
Paid tier: 100k-unlimited characters/month

Track usage in `broadcast` conversations to warn before hitting limits.
