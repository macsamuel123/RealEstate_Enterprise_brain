# Technical Requirements Document
## AI Chief of Staff

**Version:** 1.0 — Foundational
**Date:** 23 September 2026
**Companion to:** BRD/PRD v1.0

> **Note on use:** this document is written to be handed directly to Claude Code or Codex as a build spec. The architectural decisions are made here so the coding agent doesn't have to guess. Build layer by layer in the order given in §8.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────┐
│  CLIENT                                          │
│  React web app — chat UI, voice UI, dashboard    │
└────────────────────┬────────────────────────────┘
                     │ HTTPS / WebSocket
┌────────────────────▼────────────────────────────┐
│  BACKEND — Python (FastAPI)                      │
│  • Agent orchestration / router                  │
│  • Tool execution + approval gates               │
│  • Auth middleware, RBAC                         │
│  • Scheduler (briefs, proactive triggers)        │
│  • Audit logging                                 │
└──┬────────┬─────────┬──────────┬────────────┬───┘
   │        │         │          │            │
┌──▼───┐ ┌──▼────┐ ┌──▼─────┐ ┌──▼──────┐ ┌──▼─────┐
│ LLM  │ │Vector │ │Supabase│ │ Voice   │ │Connect-│
│ API  │ │ Store │ │ PG+Auth│ │ STT/TTS │ │ors     │
│      │ │Memory │ │ +RLS   │ │+Twilio  │ │(Zapier)│
└──────┘ └───────┘ └────────┘ └─────────┘ └────────┘
```

---

## 2. Stack — Components and Their Functions

| Layer | Technology | Function |
|---|---|---|
| **Front end** | React | What the customer sees: chat window, voice interface, dashboard showing brief + agent activity |
| **Back end** | Python (FastAPI) | The brain. Holds agent logic, decides which agent handles what, calls the model, enforces permissions |
| **Database + Auth** | Supabase (Postgres) | Stores everything about each client; handles login and access control; Row-Level Security keeps client data separated |
| **Memory** | Vector store (pgvector on Supabase, or Pinecone/Weaviate) | Semantic search over conversations and documents — recall by meaning, not keyword |
| **Reasoning** | Anthropic Claude / OpenAI — enterprise agreement, ZDR | The reasoning layer. Zero data retention protects client IP |
| **Speech** | ElevenLabs (TTS), Deepgram or Whisper (STT) | The Jarvis feel — streaming speech in and out |
| **Telephony** | Twilio | Real phone numbers. Inbound and outbound calls |
| **Connectors** | Zapier (phase 1) → direct APIs (phase 2) | Gmail, Calendar, CRMs, social |
| **Hosting** | Vercel (front end), Railway or Render (back end) | Deployment |
| **Secrets** | Managed vault (Doppler / Infisical / Supabase Vault) | Credentials, never in env files |
| **Payments** | Stripe | Subscription billing, usage overage |

**Why Python for the backend:** agent tooling, LLM SDKs, and orchestration libraries are strongest there. The front end being React is orthogonal — they talk over HTTP/WebSocket.

---

## 3. Data Model

Core tables (Supabase Postgres, all with RLS enabled, scoped by `org_id`):

| Table | Purpose |
|---|---|
| `orgs` | Tenant. One per customer business |
| `users` | People within an org; roles |
| `profiles` | The onboarding output: business, market, competitors, working hours, comms style, personal interests, morning ritual preferences |
| `agents` | Agent definitions — role, instructions, permitted toolset, owning org |
| `conversations` | Every exchange, channel (voice/chat/call/email), participants |
| `messages` | Individual turns; embedded for memory |
| `contacts` | People the user deals with; relationship history |
| `deals` / `pipeline` | Opportunities, stage, value, owner, last touch |
| `tasks` | Commitments and owners; due dates |
| `memories` | Durable facts and decisions, with source and reason |
| `documents` | Uploaded files, chunked + embedded |
| `connections` | OAuth tokens per external system (vaulted references, never raw) |
| `actions_log` | **Audit trail** — every tool call, agent, timestamp, input, output, approval status |
| `usage` | Voice exchanges, model tokens, per org per period — drives billing/overage |
| `briefs` | Generated daily briefs, for history and value recap |
| `benchmarks` | Anonymised aggregate metrics by vertical + geography (Phase 2) |

**Hard rule:** `benchmarks` is populated from aggregates only. No row in it is ever traceable to a single org.

---

## 4. Memory Architecture

Two related systems sharing the same vector infrastructure:

### 4.1 Document RAG
Classic retrieval. Chunk → embed → store → retrieve on relevance. Used for the client's own files: listings, market reports, contracts, brand guidelines.

### 4.2 Conversational Memory (the valuable half)
Every conversation, decision, and interaction is embedded and stored. When the user mentions a contact's name, the system pulls everything ever said about that person.

**Write path:** after each conversation, a summarisation pass extracts durable facts, decisions, commitments, and preferences → written to `memories` with source attribution → embedded.

**Read path:** on each turn, retrieve top-k from `memories` + `messages` + `documents`, filtered by `org_id`, and inject into context alongside the structured profile.

**Why this matters commercially:** this is the switching cost. Eighteen months of accumulated context is not copyable.

---

## 5. Agent Orchestration

### 5.1 What an agent is
A language model given three things:
1. **Role and instructions** — "qualify leads against these criteria"
2. **A permitted toolset** — CRM write, email send, web search, calendar
3. **Memory** — scoped to its domain plus the shared org memory

### 5.2 The router
A coordinator sits beneath everything. An event arrives (new lead, inbound call, scheduled trigger, user message), the router decides which agent owns it, and dispatches.

Example flow: lead arrives → router → qualification agent → researches company, scores against criteria → either hands to outreach agent or parks with a reason → writes outcome back to CRM → logs to `actions_log`.

### 5.3 Dynamic agent creation
User describes a need in natural language. A meta-agent converts that into an agent definition (role, instructions, toolset, schedule) and writes it to `agents`. User can then address it directly or convene multiple agents together.

**Constraint:** dynamically created agents inherit a restricted toolset by default. Any write or send capability requires explicit user approval.

### 5.4 Approval gates
Configurable per action class. Default: **read freely, write with approval, send with approval.** The user sets their own tolerance per agent as trust builds.

---

## 6. Voice Loop

```
User speaks
   → audio streams to STT (near-real-time, as they speak, not after)
   → text to agent (LLM + memory + tools)
   → agent may execute tools first (check calendar, pull contact, search)
   → response text streams to TTS
   → speech begins before the full sentence is generated (no dead air)
```

**Telephony:** for real phone calls, Twilio sits in front of this same pipeline, handling the number and bridging call audio in and out.

**Proactive / outbound:** the scheduler gives agents the ability to decide *"this is worth interrupting them for"* and trigger the same loop outbound — the agent calls the user, rather than waiting to be called.

**Latency target:** under 800ms perceived response. This is the single biggest determinant of whether it feels like a person or a walkie-talkie.

**Cost note:** ~$0.10–0.20/min combined STT+TTS. This is why voice is metered and text is not.

---

## 7. Connectors

### 7.1 Phase 1 — Zapier
Zapier is the plumbing only: triggers and connections. **The reasoning never lives in Zapier** — it lives in the Python backend.

Relevant to the pilot vertical (all have existing Zapier connectors):

| Category | Apps |
|---|---|
| Real estate CRM | Follow Up Boss, Real Geeks, kvCORE, CINC, RealScout |
| Lead sources | Zillow Tech Connect (Zillow, Trulia, HotPads, StreetEasy) |
| Email / Calendar | Gmail, Outlook, Google Calendar |
| Comms | Slack, WhatsApp, SMS |
| Other | Google Sheets, Mailchimp, Salesforce, HubSpot, DocuSign |

Zapier reaches ~9,000 apps, so most mainstream tools a customer already uses are covered.

### 7.2 Free direct routes
Gmail and Google Calendar have free APIs directly from Google — no middleman, zero ongoing cost regardless of volume. **Build these direct from day one.** Reserve Zapier for the trickier apps.

### 7.3 Phase 2 — migration off Zapier
At ~10 paying customers, or when the Zapier bill starts stinging, replace with direct API integrations. Cheaper at scale, at the cost of maintaining the plumbing yourself.

### 7.4 Phase 2 — self-building connector agent
A developer agent reads a target system's API documentation and writes the connector. **Must** pass sandbox tests and human review before touching live client data. Auto-generated code talking to someone's live business systems without a check is the single biggest risk in this product.

---

## 8. Build Order

Strictly sequential. Each layer is testable before the next begins.

1. **Auth + database** — Supabase, schema, RLS policies. Nothing works without tenant isolation being right first.
2. **Memory layer** — embeddings, write path, read path. Test recall before anything depends on it.
3. **Morning brief** — scheduled job: pull calendar + priority email + web research → compose → deliver by email/SMS. *This alone is a sellable product.*
4. **Agents** — router, standard agent set, tool execution, approval gates, audit logging.
5. **Voice** — last. Most expensive, fiddliest, highest latency risk. Everything underneath should already work in text.

**Rationale:** voice is the demo, but it is worthless on top of a system that doesn't already know anything.

---

## 9. 48-Hour Prototype Plan

| Block | Work |
|---|---|
| **Day 1 AM** | Accounts and keys: Supabase, model API, voice provider, Twilio, Stripe. Schema + RLS. |
| **Day 1 PM** | Morning brief working end to end — even if it just emails you. |
| **Day 1 evening** | Wire in your own calendar and inbox. |
| **Day 2 AM** | One agent doing real work (research or lead qualification). |
| **Day 2 PM** | The voice loop. |
| **Day 2 evening** | Point it at your own business and use it. |

Achievable in two days if you are not precious about it being pretty. **You are client zero** — live with it for a week before showing anyone.

---

## 10. Security & Governance Implementation

| Control | Implementation |
|---|---|
| Tenant isolation | Supabase Row-Level Security, every query scoped by `org_id` |
| IP protection | Zero-data-retention agreements with model providers; no training on customer data |
| Audit trail | `actions_log` — every tool call, agent, timestamp, input, output, approval |
| Access control | RBAC in backend middleware |
| Secrets | Managed vault; OAuth tokens stored as vaulted references |
| Approval gates | Default: read free, write and send require approval |
| Encryption | TLS in transit, at-rest encryption on Supabase |
| Connector safety | Sandbox + tests + human review before production |
| SOC 2 | **Deferred.** Practices implemented now so certification later is documentation, not rebuild |

---

## 11. Running Cost Estimates

### Single pilot version (pre-revenue)

| Item | Monthly |
|---|---|
| LLM API | $50–300 |
| Zapier / Make | $20–75 |
| Voice (light use) | $50–200 |
| Gmail / Calendar APIs | Free |
| Database / hosting | $25–50 |
| **Total** | **$150–600** |

### At 10 SaaS + 1 Custom

| Item | Monthly |
|---|---|
| Hosting, DB, Zapier | $150 |
| Model usage (11 clients) | $150 |
| Voice + telephony | $200 |
| **Total** | **~$500** |

### At 100 SaaS clients

| Item | Monthly |
|---|---|
| Model usage (~$8–15/client) | $1,000–1,500 |
| Voice (~$10/client, capped) | $1,000 |
| Infrastructure (non-linear) | $300–500 |
| **Total** | **$2,500–3,000** |

Against $12,500/month revenue at $125 — roughly **75–80% margin.**

**Contrast — 100 custom builds:** per-client running costs are similar, but maintaining 100 separate configurations realistically means hiring 2–3 people, adding $10–20k/month in labour. Margins collapse. **This is why SaaS is the volume play and custom is the premium exception, not the default.**

### Per-agent-task costs
A single lead qualification runs ~$0.10–0.30 in model usage (agents reason in multiple steps, so they cost more than simple automations). 1,000 leads/month ≈ $100–300. **This is the number to watch.**

---

## 12. Build Approach

Use **Claude Code or Codex** as the implementation engine. Feed this document as the spec and build layer by layer per §8.

What the coding agent will do well: backend scaffolding, agent logic, database schema, API wiring, front-end components.

What it will not do: make the architectural and commercial decisions. Those are made in this document and the BRD — which is exactly why both exist before a line of code.
