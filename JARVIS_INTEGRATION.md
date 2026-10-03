# JARVIS Dashboard Integration Plan

**Goal:** Adapt AndrewKochulab/jarvis-dashboard as the UI foundation for AI Chief of Staff

**Status:** Planning → Implementation

---

## Executive Summary

The JARVIS dashboard is a modular, multi-platform command center with proven:
- Real-time monitoring architecture
- Voice command system (TTS/STT)
- Configurable JSON-driven layout
- Widget-based component model
- Cross-platform support (Obsidian, macOS, iOS)

We will fork it, customize widgets for real estate operations, and connect it to our FastAPI backend.

**Benefit:** 12 weeks of production-grade UI work already done; we adapt, not rebuild.

---

## Architecture Overview

### JARVIS Widget System

```
src/
├── core/                  # State management, routing, lifecycle
├── services/              # File I/O, process management, voice
├── widgets/               # 13 modular components
│   ├── voice-command/     # Speech-to-text + Claude interaction
│   ├── live-sessions/     # Real-time monitoring
│   ├── agent-cards/       # Agent status display
│   ├── activity-analytics # 30-day heatmap + stats
│   ├── system-diagnostics # Health metrics
│   └── [... 8 more ...]
└── config/                # JSON-based configuration

shared/                   # Platform adapters (Obsidian, macOS, iOS)
companion/                # WebSocket server for mobile
ios/                      # Swift UI app
macos/                    # Tauri 2.0 app
```

### How It Works

1. **Config-driven:** `config.json` defines widgets, layout, themes, voice settings
2. **Context object:** Shared `ctx` object passes state between widgets
3. **Module loading:** No import/export — uses `new Function("ctx", code)` for evaluation
4. **Platform adapters:** Abstract file system, voice, process management

---

## Integration Strategy

### Phase 1: Fork & Setup (2-3 days)

```bash
# 1. Fork the repo
git clone https://github.com/AndrewKochulab/jarvis-dashboard.git
cd jarvis-dashboard
git remote rename origin upstream

# 2. Create new origin pointing to RealEstate_Enterprise_brain
git remote add origin <your-repo>
git push -u origin main

# 3. Copy to frontend directory
cp -r . ../RealEstate_Enterprise_brain/frontend/
```

### Phase 2: Widget Customization (1-2 weeks)

**Keep (minimal adaptation):**
- `voice-command` — Already perfect for our voice HUD; just rewire to our backend
- `header` / `footer` — Rename to "Chief of Staff Dashboard"
- `quick-launch` — Customized for command palette

**Adapt (modify):**
- `agent-cards` → Rename to `agent-squad` (add status, tool permissions, live metrics)
- `system-diagnostics` → Repurpose as `operational-heartbeat` (business metrics, anomalies)
- `live-sessions` → Rename to `approval-queue` (show pending tool actions)
- `activity-analytics` → Keep but adapt for real estate metrics

**Remove (not needed):**
- `focus-timer` — Out of scope
- `mission-control` — Replace with agent creation panel
- `communication-link` — Not needed for initial version

**Build New:**
- `operational-heartbeat` — Business vital signs (lead velocity, response time, pipeline, anomalies)
- `approval-gate-feed` — Approval queue with auth cards
- `memory-matrix` — Spatial graph of stored memories
- `competitor-radar` — Market intelligence display

### Phase 3: Backend Integration (1-2 weeks)

**Adapt services to call FastAPI instead of Claude CLI:**

```javascript
// Before (JARVIS talks to Claude CLI)
services.command.execute("claude code --run script.py")

// After (Enterprise Brain talks to FastAPI)
services.api.post("http://localhost:8000/api/agents/dispatch", {
  event_type: "user_message",
  event_data: { message: userInput }
})
```

**New adapters needed:**

| Service | Current | New |
|---|---|---|
| `command` | Claude CLI (local) | FastAPI (HTTP) |
| `voice` | Local Piper/Say | ElevenLabs (TTS) + Whisper (STT) |
| `projects` | File system scan | Supabase query |
| `sessions` | Process monitor | WebSocket to backend |

### Phase 4: Configuration (3-5 days)

**Custom config.json for Enterprise Brain:**

```json
{
  "name": "AI Chief of Staff",
  "subtitle": "Calgary Operations — Shawn Getty",
  "theme": "cybernetic-executive-deck",
  "colors": {
    "primary": "#00F0FF",
    "accent": "#8A2BE2",
    "success": "#00FF87",
    "warning": "#FFB800",
    "critical": "#FF2E63"
  },
  "layout": [
    "header",
    "phase-indicator",
    {
      "type": "grid",
      "columns": 2,
      "widgets": [
        "operational-heartbeat",
        "agent-squad",
        "approval-gate-feed"
      ]
    },
    "memory-matrix",
    "voice-command",
    "footer"
  ],
  "voice": {
    "enabled": true,
    "tts_engine": "elevenlabs",
    "stt_engine": "whisper",
    "personality": "chief-of-staff"
  },
  "api": {
    "base_url": "http://localhost:8000",
    "websocket_url": "ws://localhost:8000"
  }
}
```

---

## File Structure After Integration

```
frontend/
├── src/
│   ├── core/                    # JARVIS core (state, routing)
│   ├── services/
│   │   ├── command.js           # → FastAPI adapter
│   │   ├── voice.js             # → ElevenLabs + Whisper adapter
│   │   ├── api.js               # NEW: HTTP client to backend
│   │   └── websocket.js         # NEW: Real-time subscriptions
│   ├── widgets/
│   │   ├── voice-command/       # KEEP: Adapted to our voice HUD
│   │   ├── agent-squad/         # ADAPT: From agent-cards
│   │   ├── operational-heartbeat/ # NEW
│   │   ├── approval-gate-feed/  # NEW
│   │   ├── memory-matrix/       # NEW
│   │   └── [... others ...]
│   ├── adapters/
│   │   ├── supabase.js          # NEW: Data queries
│   │   ├── api.js               # NEW: HTTP calls
│   │   └── config.js            # Config loader
│   └── config/
│       ├── config.example.json  # Defaults
│       ├── config.json          # Personal overrides
│       └── config.local.json    # Secrets (gitignored)
├── package.json
└── README.md
```

---

## API Contract: Frontend ↔ Backend

### Voice Command Flow

```
Frontend (voice-command widget)
  ↓ (WebSocket)
Backend (agent orchestrator)
  → Routes to appropriate agent
  → Executes agent logic
  → Calls tools (CRM, email, etc)
  ↓ (WebSocket stream)
Frontend
  ← Receives response in real-time
  ← Updates transcript
  ← Streams TTS waveform
```

### Data Binding: Widgets ↔ Backend

Each widget subscribes to a data stream:

```javascript
// Operational Heartbeat widget subscribes to:
ctx.api.subscribe("/api/operational-heartbeat", (data) => {
  ctx.state.systemIntegrity = data.integrity_score;
  ctx.state.leadVelocity = data.response_time_minutes;
  ctx.state.anomalies = data.active_anomalies;
  ctx.render();
});

// Approval Gate Feed subscribes to:
ctx.api.subscribe("/api/actions-log?status=pending", (actions) => {
  ctx.state.pendingApprovals = actions;
  ctx.render();
});
```

### Backend Endpoints to Wire

| Endpoint | Widget | Purpose |
|---|---|---|
| `GET /api/operational-heartbeat` | operational-heartbeat | Live business metrics |
| `GET /api/agents` | agent-squad | Agent roster + status |
| `GET /api/actions-log?status=pending` | approval-gate-feed | Pending approvals |
| `POST /api/actions-log/:id/approve` | approval-gate-feed | Approve tool action |
| `POST /api/actions-log/:id/deny` | approval-gate-feed | Reject tool action |
| `WS /ws/agent-stream` | voice-command | Real-time agent responses |
| `GET /api/memories` | memory-matrix | Retrieve stored facts |
| `GET /api/conversations/:id` | voice-command | Chat history |

---

## Implementation Timeline

### Week 1: Setup & Core Adaptation
- [ ] Fork JARVIS repo
- [ ] Strip down to essential widgets
- [ ] Wire voice-command to our backend
- [ ] Adapt config.json structure

### Week 2: Widget Customization
- [ ] Build operational-heartbeat widget
- [ ] Build approval-gate-feed widget
- [ ] Adapt agent-cards → agent-squad
- [ ] Create memory-matrix widget

### Week 3: Backend Integration
- [ ] Implement WebSocket server in FastAPI
- [ ] Create `/api/` endpoints for each widget
- [ ] Wire Supabase queries to widgets
- [ ] Real-time subscription system

### Week 4: Polish & Testing
- [ ] Theme customization (cybernetic deck)
- [ ] Voice integration (ElevenLabs + Whisper)
- [ ] Mobile responsive (if needed)
- [ ] E2E testing

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| JARVIS uses unusual module system (no import/export) | Document module contract; all our new widgets follow pattern |
| Voice system tied to local TTS (Piper/Say) | Adapter layer abstracts TTS; swap ElevenLabs easily |
| Multi-platform code (Obsidian, macOS, iOS) adds complexity | Start with web-only; platform code stays untouched |
| Config cascade might conflict with our backend config | Separate frontend config from backend; clear precedence |

---

## Success Criteria

✅ **Week 1:** JARVIS builds, runs, connects to our FastAPI backend  
✅ **Week 2:** Operational Heartbeat shows live system metrics  
✅ **Week 3:** Approval Queue displays pending tool actions  
✅ **Week 4:** Voice HUD works end-to-end (STT → Agent → TTS)  
✅ **Final:** Shawn can use dashboard + voice to run business operations  

---

## Next Steps

1. **Confirm:** Do you want to proceed with this JARVIS fork approach?
2. **Setup:** I'll fork the repo and create the integration structure
3. **Backend:** Meanwhile, build the WebSocket server + endpoints for widgets
4. **Frontend:** Start with voice-command widget wired to your agents

Should I start the fork now?
