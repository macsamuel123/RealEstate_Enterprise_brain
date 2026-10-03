# 🎯 Dashboard Quick Start

Your **AI Chief of Staff** dashboard is now running on localhost!

---

## 🚀 Access the Dashboard

**Open in your browser:**
```
http://localhost:5173
```

---

## What You're Looking At

This is the **Cybernetic Executive Deck** — a JARVIS-inspired command center with real-time monitoring of your business operations.

### Dashboard Panels

1. **⚕️ Operational Heartbeat**
   - System Integrity: Real-time health score (target: >85%)
   - Response Time: Lead response speed (target: <60 min)
   - Pipeline Value: Active deal value
   - Anomalies: Issues flagged for attention

2. **🤖 Agent Squad**
   - Research Agent — Market intelligence
   - Lead Qualifier — Inbound processing
   - Content Creator — Blog & social
   - Communications — Calls & email
   - Op. Heartbeat — Health monitoring
   - Concierge — Personal assistant

3. **⚠️ Approval Queue**
   - Pending tool actions waiting for your authorization
   - Click to approve or deny agent actions
   - Built-in audit trail for compliance

4. **🎤 Voice Command**
   - (Coming soon) Full voice interaction with agents
   - Speech-to-text + natural language understanding
   - Real-time transcript

5. **📋 Recent Activity**
   - Live log of what agents are doing
   - Quick summary of today's operations

---

## 🔧 Customization

The dashboard is controlled via `frontend/src/config/config.json`. Edit to customize:

```json
{
  "dashboard": {
    "title": "⚡ Chief of Staff",
    "subtitle": "Your Business Name"
  },
  "theme": {
    "accent": "#00F0FF",    // Cyan neon
    "purple": "#8A2BE2",    // Violet
    "green": "#00FF87"      // Emerald
  },
  "widgets": {
    "operationalHeartbeat": {
      "refreshInterval": 5000  // Update every 5 seconds
    }
  }
}
```

---

## 📡 Backend Connection

The dashboard expects your FastAPI backend running on:
```
http://localhost:8000
```

If your backend is running elsewhere, update in `config.json`:
```json
{
  "api": {
    "base_url": "http://your-backend:8000",
    "websocket_url": "ws://your-backend:8000"
  }
}
```

---

## 🛠️ Development

### Stop the server
```bash
# Press Ctrl+C in the terminal, or:
pkill -f "vite"
```

### Restart the server
```bash
cd frontend
npm run dev
```

### Build for production
```bash
npm run build
# Output: frontend/dist/
```

---

## 📝 What's Next

1. **Wire the backend** — Implement WebSocket endpoints so metrics update live
2. **Enable voice** — Connect to ElevenLabs (TTS) + Whisper (STT)
3. **Add approvals** — Real approval logic tied to agent actions
4. **Deploy** — Send to Vercel or Railway

---

## 🐛 Troubleshooting

### Dashboard shows "System Error"
- Check browser console (F12) for error messages
- Ensure `frontend/src/config/config.json` exists and is valid JSON
- Verify file paths are correct

### "Cannot connect to backend"
- Confirm FastAPI is running on `http://localhost:8000`
- Check CORS settings in `backend/app/main.py`

### Widgets not updating
- Dashboard currently shows static mock data
- Real data comes from backend integration (Week 3 of JARVIS_INTEGRATION.md)

---

## 📚 Related Docs

- [JARVIS Integration Plan](./JARVIS_INTEGRATION.md) — Full technical roadmap
- [TRD — Technical Requirements](./02-TRD.md) — Architecture & build order
- [BRD — Business Context](./01-BRD-PRD.md) — Product vision
- [Build Status](./BUILD_STATUS.md) — What's done & what's next

---

**Status:** ✅ UI running | 🔲 Backend wiring | 🔲 Voice enabled | 🔲 Production ready

🎙️ **Next milestone:** Wire operational-heartbeat widget to real `/api/operational-heartbeat` endpoint
