# Demo Setup for Shawn Getty

**Goal:** 20-minute walkthrough showing AI Chief of Staff in action

---

## Quick Start

### 1. Seed Demo Data

```bash
# Run once to populate Getty Group with demo data
python backend/scripts/seed_demo.py
```

**Creates:**
- Org: Getty Group
- User: Shawn Getty
- 20 recruits (3 flagged as silent)
- 30 leads in pipeline
- 10+ conversations with memories
- All 8 system agents

### 2. Start Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Backend running at: `http://localhost:8000`

### 3. Start Frontend

```bash
cd frontend
npm run dev
```

Frontend running at: `http://localhost:5173`

### 4. Open Dashboard

```
http://localhost:5173
```

You should see:
- ⚡ JARVIS-style dashboard
- Morning Brief widget (showing seeded data)
- Voice Command (animated)
- Agent Squad (8 agents)
- Approval Queue (with 3 mock items)
- Recent Activity (live log)

---

## Demo Script

**Duration: 20 minutes**

See: `docs/DEMO_SCRIPT.md` for full walkthrough

### Quick Version

1. **Morning Brief** (2 min)
   - Show seeded brief (personal + business)
   - Explain agent orchestration

2. **Voice Command** (3 min)
   - Speak: "What's the status with my recruiting pipeline?"
   - Watch agents work
   - Hear response via ElevenLabs TTS

3. **Approval Queue** (2 min)
   - Show 3 pending approvals
   - Tap "Approve" on one
   - Watch approval flow + logging

4. **Lead Form** (2 min)
   - Fill test form: `frontend/demo-form.html` (coming)
   - Watch qualification in <10s
   - Show Recent Activity updating

5. **Pre-Call Briefing** (2 min)
   - Show context before call
   - Display memories + history

6. **Voice Call** (5 min)
   - Real call or mock audio
   - Show agent working invisibly
   - Post-call summary drafted

7. **Custom Agent** (1 min)
   - Show Agent Builder
   - Create "Davids Group Watcher"

---

## URLs for Demo

| Page | URL | Purpose |
|------|-----|---------|
| **Dashboard** | http://localhost:5173 | Main UI |
| **Approval** | http://localhost:5173/approval.html | Mobile approval page |
| **Lead Form** | http://localhost:5173/demo-form.html | Inbound lead form (TBA) |
| **API Health** | http://localhost:8000/health | Backend status |

---

## API Endpoints

### Voice
```bash
# Send audio file
curl -X POST http://localhost:8000/api/voice/message \
  -F "audio=@test.wav"

# WebSocket (real-time)
ws://localhost:8000/api/voice/stream
```

### OpenAI-Compatible (for Vapi/Retell)
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-opus-5-5",
    "messages": [{"role": "user", "content": "Pipeline status?"}]
  }'
```

### Agent Execution
```bash
curl -X POST http://localhost:8000/api/agents/execute \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_role": "lead_qualification",
    "task": "Qualify Sarah Johnson - 3-bed SW Calgary, $450k, 60 days"
  }'
```

---

## Troubleshooting

### "Can't connect to backend"
```bash
# Check backend is running
curl http://localhost:8000/health

# If not: make sure you're in backend/ directory
cd backend
python -m uvicorn app.main:app --reload
```

### "Database error"
```bash
# Make sure Supabase credentials are in .env
cat .env | grep SUPABASE

# If empty, ask for credentials from project setup
```

### "Voice not working"
```bash
# Check API keys in .env
echo $OPENAI_API_KEY
echo $ELEVENLABS_API_KEY

# If empty, add keys to .env
```

### "Demo data not seeding"
```bash
# Run seed script with debug
python backend/scripts/seed_demo.py --verbose

# Check database has getty-group org
# If not, database connection issue
```

---

## What to Say During Demo

### Opening
> "Shawn, I want to show you something different. This isn't a CRM replacement — it's a Chief of Staff AI that works invisible in the background. You talk to it like a person. It qualifies leads in <10 seconds, remembers everything, and logs every action for compliance. Let me show you."

### Morning Brief
> "Overnight, this system worked while you slept. It read your calendar, searched the market, tracked competitors, and flagged anomalies. All orchestrated by invisible agents working together."

### Voice Command
> "Every word you speak gets routed through specialist agents. You don't click — you talk. No transcription apps, no manual notes. Everything is remembered."

### Approval Queue
> "You stay in control. Every write gets approved by you. One tap and it's done. Audit log tracks everything."

### Lead Form
> "Leads don't wait. From first contact to qualified + reply drafted in <10 seconds. No lost time."

### Pre-Call Briefing
> "Before a call, you're completely briefed. Six months of history in 2 seconds. You just close."

### Custom Agent
> "You don't need engineers. Ask for an agent in plain English and it's deployed tomorrow."

---

## Post-Demo: Next Steps

**If Shawn is interested:**

1. **"Let's make this real for your CRM"**
   - Which CRM do you use? (Zapier or direct API)
   - What workflows do you want automated?

2. **"Let's run a pilot"**
   - 1 week: You use it with real leads
   - We gather metrics (response time, lead quality)
   - You give us feedback

3. **"Then you're our case study"**
   - Document metrics (before/after)
   - Feature you in launch
   - $5k credit toward annual SaaS

---

## Files Reference

- `DEMO_SCRIPT.md` — Full 7-scene walkthrough
- `backend/scripts/seed_demo.py` — Populate demo data
- `backend/app/agents/executor.py` — Real agent delegation
- `backend/app/routers/llm.py` — OpenAI-compatible endpoint
- `frontend/approval.html` — Mobile approval page
- `.env.example` — Copy to `.env` and fill API keys

---

## Tips for Smooth Demo

✅ **Before demo:**
- Run seed_demo.py the morning of
- Test voice (say something into dashboard)
- Test approval approval (approve a queue item)
- Have phone ready for approval page test
- Backup internet (hotspot)

✅ **During demo:**
- Speak clearly (Whisper STT works best with clear audio)
- Give agents time to think (2-3 sec, don't interrupt)
- Show dashboard updates in real-time
- Point out Recent Activity updates
- Emphasize <10s lead qualification

✅ **After demo:**
- Ask "What would make this real for you?"
- Listen for CRM needs, workflow requests
- Offer pilot (1 week, real usage)
- Pitch case study + credit

---

**Goal: Show working product, get pilot commitment, make Shawn the launch case study.**

Good luck! 🚀
