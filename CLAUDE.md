# CLAUDE.md — Project Context & Conventions

> Guidance for Claude Code and future developers on this codebase.

---

## Project Overview

**AI Chief of Staff** — Voice-first AI partner for real estate agents. Learns the business, runs operations (answering leads, following up, writing content, briefing owner), proactively helps.

- **Pilot customer:** Shawn Getty, Getty Group, Calgary AB
- **Business model:** SaaS ($125/mo) + Custom Build (quoted)
- **Target:** Real estate agents, small teams, solo operators with lead flow and personal brand

See [01-BRD-PRD.md](01-BRD-PRD.md) for full business context.

---

## Architecture & Build Order

**Strict layer-by-layer build per [02-TRD.md](02-TRD.md) §8:**

1. ✅ **Layer 1 — Auth + Database** (Supabase schema, RLS, tenant isolation by `org_id`)
2. ✅ **Layer 2 — Memory** (Embeddings, semantic search, durable facts)
3. ✅ **Layer 3 — Morning Brief** (Generator, deliverer, scheduler)
4. 🚧 **Layer 4 — Agents** (Router, standard agents, tool execution, approval gates)
5. ⏳ **Layer 5 — Voice** (STT/TTS, phone calls, latency optimization)

**Rationale:** Each layer must be testable before the next starts. Voice is last because it's expensive/fiddly.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React + TypeScript + Vite | Type-safe, fast dev, modern tooling |
| Backend | FastAPI + Python | Best agent/LLM SDKs, async-first |
| Database | Supabase (Postgres) | Built-in Auth, RLS, pgvector, vault |
| LLM | Anthropic (primary) + OpenAI (fallback) | Redundancy, both request ZDR for IP protection |
| Embeddings | OpenAI text-embedding-3-small | 1536 dims, semantic search via pgvector |
| Voice TTS | ElevenLabs | Natural-sounding, Jarvis feel |
| Voice STT | OpenAI Whisper | Already in OpenAI account, fast |
| Telephony | Twilio | Real phone numbers, inbound/outbound |
| Hosting | Vercel (frontend) + Railway (backend) | Simple, good DX, affordable |

---

## Key Design Decisions (Locked)

1. **Tenant isolation = `org_id` + Supabase RLS**
   - Every table row belongs to exactly one org
   - Every RLS policy filters by `org_id`
   - Impossible to accidentally leak one customer's data to another

2. **Zero-data-retention with LLM providers**
   - Sign ZDR agreements with Anthropic & OpenAI
   - Customer IP stays customer IP — core competitive advantage

3. **Memory as switching cost**
   - After 6-12 months, the system knows everything about the user
   - Competitors can't copy that context
   - Even if product features get copied, memories can't

4. **Approval gates by default**
   - Read freely, write/send requires approval
   - User trains their tolerance as trust builds
   - Audit log records every action (mandatory compliance)

5. **No feature flags / backwards-compat shims**
   - Build for present requirements only
   - Three similar lines OK, premature abstraction not

---

## Naming & Conventions

### Database / Models
- **Tables:** singular snake_case (`user`, `agent`, `conversation`, not `users`)
- **Columns:** snake_case, clear (e.g. `auth_user_id` not `uid`, `org_id` not `oid`)
- **Foreign keys:** `{table_name}_id` (e.g. `user_id`, `org_id`)
- **Enums:** PascalCase classes in Python, lowercase in SQL

### Backend
- **Routers:** `backend/app/routers/{feature}.py` (e.g. `briefs.py`, `agents.py`)
- **Models:** `backend/app/models.py` (single file, ~1000 lines)
- **Services/managers:** `backend/app/{feature}/manager.py` (e.g. `MemoryManager`)
- **Config:** `backend/app/config.py` (one settings object)
- **Database:** `backend/app/database.py` (Supabase client)

### Frontend
- **Components:** `frontend/src/components/{name}.tsx`
- **Pages:** `frontend/src/pages/{name}.tsx`
- **State:** Zustand stores in `frontend/src/store/{feature}.ts`
- **API client:** `frontend/src/lib/api.ts`

### Commits
- **Format:** Clear verb + what changed
- **Example:** "Implement memory recall via semantic search" not "Update memory.py"
- **Attribution:** Include `Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>`

---

## What NOT to Do

1. **Don't build backwards-compat shims**
   - If something changes, just change it (this is pre-1.0)
   - No feature flags for "old vs new" logic

2. **Don't add error handling for impossible cases**
   - Trust Supabase RLS (won't let user access wrong org)
   - Trust FastAPI validation (pydantic catches bad input)
   - Only validate at **system boundaries** (external APIs, user input)

3. **Don't create pre-emptive abstractions**
   - "What if we need to support multiple embedding providers?"
   - Build for OpenAI. If we change, we'll refactor when we know.

4. **Don't write multi-paragraph docstrings or comment blocks**
   - One line max, only if WHY is non-obvious
   - Code should read like prose — names do the work

5. **Don't commit secrets or API keys**
   - Use `.env` files (in `.gitignore`)
   - Supabase Vault for customer secrets (OAuth tokens, CRM keys)

6. **Don't skip the build order**
   - Layer 4 agents depend on Layer 2 memory
   - Layer 5 voice depends on Layer 4 agents
   - Short-cutting will cause rework

---

## Before You Start Coding

### Every Build Session

1. **Check git status** — unstaged changes? Know why.
2. **Read the relevant TRD section** — know the requirement.
3. **Know the open questions** — don't guess.

### Before committing

1. **Run type check:** `python -m pytest` (backend) or `npm run type-check` (frontend)
2. **Test manually** — if you added a route, hit it. If a memory lookup, test recall.
3. **Clean up:** No console.logs, debug code, or TODOs you added carelessly.

---

## Open Questions

From [01-BRD-PRD.md](01-BRD-PRD.md) §12:

1. **What CRM does Shawn use?** — Affects initial connector setup (Follow Up Boss / Real Geeks / kvCORE / CINC / RealScout)
2. **Voice allowance cap?** — 30 exchanges/month is the guess; lock after pilot data
3. **Product name?** — Not yet decided
4. **Legal entity & T&Cs** — Needed before customer data touches servers

---

## How to Continue

### Next: Layer 4 (Agents)

1. **Expand orchestrator** in `backend/app/agents/orchestrator.py`
   - Implement `_detect_intent()` using LLM
   - Wire up agent dispatch to actual tool calls
   - Build approval-gate flow

2. **Create tool implementations** in `backend/app/tools/`
   - CRM read/write (lead_qual, follow_up, update)
   - Email draft/send
   - Calendar read/write
   - Web search
   - Analytics read

3. **Add agent routers** in `backend/app/routers/`
   - `/agents` — list, create, update
   - `/conversations` — message history, send message
   - `/tools` — available tools and their parameters

4. **Test agents locally** with manual API calls before wiring voice

### Then: Layer 5 (Voice)

1. **STT pipeline** — Whisper → text → agent
2. **TTS pipeline** — agent text → ElevenLabs → audio stream
3. **Latency optimization** — aim for <800ms perceived response
4. **Twilio integration** — answer calls, detect intent, route to agent

---

## Debugging Checklist

**Backend won't start?**
- Is venv activated?
- Are all env vars in `.env` filled?
- Is Supabase project URL correct?
- Run `python -c "from app.main import app"` to check imports

**Database queries fail?**
- Check RLS policies — user might not have access to this org
- Check `org_id` is passed correctly in query
- Verify table name matches schema exactly (case-sensitive)

**LLM calls failing?**
- Check API key in `.env` doesn't have extra spaces
- Verify ZDR agreement is active (takes 24h)
- Check account has quota left
- Watch network tab — are requests reaching API?

**Memory recall empty?**
- Did you write to `embeddings` column or just `fact`?
- Is similarity threshold too high?
- Check that top-k is not capped too low

---

## Resources

- **Business:** [01-BRD-PRD.md](01-BRD-PRD.md)
- **Tech:** [02-TRD.md](02-TRD.md)
- **Setup:** [SETUP.md](SETUP.md)
- **Architecture:** [README.md](README.md)
- **Commit messages:** Check git log for style
