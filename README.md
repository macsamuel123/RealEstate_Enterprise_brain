# AI Chief of Staff — Real Estate Edition

A voice-first, proactive AI partner that learns a real estate agent's business and runs the operational layer. Answers leads in minutes, follows up automatically, writes content, and diagnoses where the business is leaking.

**Status:** Pre-build. Pilot customer identified (Shawn Getty, Getty Group, Calgary).

---

## Quick Links

- **Business & Product Requirements:** [01-BRD-PRD.md](01-BRD-PRD.md)
- **Technical Requirements & Stack:** [02-TRD.md](02-TRD.md)
- **Marketing & Sales Plan:** [03-Marketing-Sales-Plan.md](03-Marketing-Sales-Plan.md)
- **Promo Video Script:** [04-Video-Script.md](04-Video-Script.md)
- **Tools & API Keys Reference:** [.claude/plans/i-need-to-build-nifty-sunbeam.md](.claude/plans/i-need-to-build-nifty-sunbeam.md)

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (React)                               │
│  Chat UI, voice UI, dashboard                   │
└────────────────────┬────────────────────────────┘
                     │ HTTPS / WebSocket
┌────────────────────▼────────────────────────────┐
│  Backend (FastAPI + Python)                      │
│  Agent orchestration, tool execution, auth      │
└──┬────────┬─────────┬──────────┬────────────┬───┘
   │        │         │          │            │
┌──▼───┐ ┌──▼────┐ ┌──▼─────┐ ┌──▼──────┐ ┌──▼─────┐
│ LLM  │ │Vector │ │Supabase│ │ Voice   │ │Connect-│
│API   │ │ Store │ │PG+Auth │ │STT/TTS  │ │ors     │
│      │ │Memory │ │ +RLS   │ │+Twilio  │ │(Zapier)│
└──────┘ └───────┘ └────────┘ └─────────┘ └────────┘
```

**Stack:**
- Frontend: React + TypeScript
- Backend: FastAPI + Python
- Database: Supabase (Postgres + Auth + RLS + pgvector + Vault)
- LLM: Anthropic Claude (primary) + OpenAI (fallback)
- Voice: ElevenLabs (TTS) + OpenAI Whisper (STT) + Twilio (telephony)
- Hosting: Vercel (frontend) + Railway (backend)
- Payments: Stripe
- Connectors: Zapier (phase 1)

---

## Getting Started

### 1. Setup (Day 1 AM)

Create accounts and collect API keys. See [Tools & API Keys Reference](.claude/plans/i-need-to-build-nifty-sunbeam.md) for the full checklist.

**Required:**
```bash
# 1. Supabase project
# 2. Anthropic API key (request ZDR agreement)
# 3. OpenAI API key (request ZDR agreement)
# 4. Google OAuth credentials (Gmail + Calendar)
```

Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

### 2. Install dependencies

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 3. Database schema + migrations

```bash
cd supabase
# Use Supabase CLI or apply migrations manually
supabase link  # Link to your project
supabase push  # Apply all migrations
```

---

## Build Order (per TRD §8)

Strictly sequential — each layer testable before the next begins:

1. **Auth + Database** (Layer 1)
   - Supabase schema with RLS policies
   - Tenant isolation by `org_id`
   - Nothing works without this being right first

2. **Memory Layer** (Layer 2)
   - Vector embeddings for semantic recall
   - Conversation history stored + embedded
   - Write and read paths tested

3. **Morning Brief** (Layer 3)
   - Scheduled job: pull calendar + email + web research
   - Compose and deliver by email/SMS
   - *This alone is a sellable product*

4. **Agents** (Layer 4)
   - Router: which agent handles what
   - Standard agent set (research, lead qual, content, comms, operational heartbeat, concierge)
   - Tool execution + approval gates
   - Audit logging

5. **Voice** (Layer 5) — Built last
   - Most expensive, fiddliest, highest latency risk
   - Everything underneath should already work in text

---

## 48-Hour Prototype (TRD §9)

| Block | Work |
|---|---|
| **Day 1 AM** | Accounts + Supabase schema + RLS |
| **Day 1 PM** | Morning brief working end-to-end |
| **Day 1 evening** | Wire in your own calendar + inbox |
| **Day 2 AM** | One agent doing real work (research or lead qualification) |
| **Day 2 PM** | Voice loop |
| **Day 2 evening** | Point it at your own business and use it |

---

## Project Structure

```
.
├── backend/                    # FastAPI + Python
│   ├── app/
│   │   ├── main.py            # FastAPI app entry
│   │   ├── agents/            # Agent definitions + orchestration
│   │   ├── tools/             # Tool implementations
│   │   ├── db/                # Database + ORM models
│   │   ├── auth/              # Authentication + RBAC
│   │   ├── connectors/        # External integrations
│   │   └── utils/             # Shared utilities
│   ├── requirements.txt
│   └── tests/
├── frontend/                   # React + TypeScript
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page routes
│   │   ├── lib/               # Utilities + Supabase client
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── supabase/                   # Database migrations
│   ├── migrations/
│   └── schema.sql
├── docs/
│   └── 01-BRD-PRD.md
│   └── 02-TRD.md
│   └── 03-Marketing-Sales-Plan.md
│   └── 04-Video-Script.md
├── .env.example
├── .gitignore
└── README.md                   # You are here
```

---

## Key Decisions Locked

- ✅ Two products: SaaS ($125/mo) + Custom Build (quoted)
- ✅ Voice-first, proactive, personal-then-business morning ramp
- ✅ Operational Heartbeat as a named headline feature
- ✅ Cross-client benchmarking as the long-term moat
- ✅ Tenant isolation via Supabase RLS (every query scoped by `org_id`)
- ✅ Zero-data-retention with model providers (IP protection)
- ✅ Approval gates by default: read free, write + send require approval
- ✅ Zapier for phase-1 connectors; direct APIs at ~10 customers

---

## Open Questions (per BRD §12)

1. **Shawn's CRM?** Which of Follow Up Boss / Real Geeks / kvCORE / CINC / RealScout does he use? Affects the initial connector setup.
2. **Voice allowance?** 30 exchanges/month included — lock the actual number after pilot data.
3. **Product name?** Not yet decided.

---

## Getting Help

- Questions about the business/product? See [01-BRD-PRD.md](01-BRD-PRD.md)
- Questions about the tech stack? See [02-TRD.md](02-TRD.md)
- Questions about the build order? See TRD §8–9
- Questions about tools/keys? See [.claude/plans/i-need-to-build-nifty-sunbeam.md](.claude/plans/i-need-to-build-nifty-sunbeam.md)

---

**Version:** 0.1 (pre-build)  
**Last updated:** 2026-09-23  
**Owner:** Eric Omughelli
