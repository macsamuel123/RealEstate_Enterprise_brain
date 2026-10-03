# Layer 4: Agent Execution Framework ✅

**Status:** Architecture complete, stubs ready for implementation, end-to-end testable

---

## What We Built

### 1. **8 Standard Agents** (backend/app/agents/orchestrator.py)

| Agent | Role | Model | Permissions |
|-------|------|-------|-------------|
| **Orchestrator** | Chief of Staff, routes all tasks | Haiku→Sonnet | Read everything, delegate only |
| **Memory Scribe** | Extracts facts post-conversation | Haiku | Memory write only |
| **Research** | Market/competitor intelligence | Sonnet (Batch) | Web search, news fetch |
| **Pipeline** | Lead qualification & follow-up | Sonnet | CRM read, gated CRM write |
| **Content** | Blogs, social, newsletters | Sonnet | Draft only, no publish |
| **Heartbeat** | Business health monitoring | Haiku | Read-only analytics |
| **Communications** | Email, SMS, calls, scheduling | Sonnet/Haiku | Send (all gated), drafts free |
| **Agent Builder** | Custom agent configs from requests | Opus | Agent definition write |

**Model tiers optimized for:**
- Routing cost (Haiku for every-turn decisions)
- Latency (Haiku for live calls <500ms)
- Batch pricing (Research runs overnight)
- Quality (Sonnet for writing, Opus for rare critical work)

---

### 2. **Agent-to-Agent Protocol** (backend/app/agents/protocol.py)

```python
AgentMessage(
    message_type: REQUEST | RESULT | DELEGATE | ERROR
    from_agent_role: str
    to_agent_role: str
    task_description: str
    context: Dict  # contact_id, deal_id, conversation_id, custom data
    status: "pending" | "success" | "error"
    result: Dict
    error_message: Optional[str]
)
```

**Supported message types:**
- `REQUEST`: One agent asks another to do something
- `RESULT`: Agent returns findings to requestor
- `DELEGATE`: Orchestrator assigns task to specialist
- `ERROR`: Agent reports failure

**Example flow:**
```
Orchestrator: delegate to Research
  → "Research competitor XYZ market share"
    
Research: (executes, finds data)
  → result to Orchestrator
    
Orchestrator: (gets result) delegate to Communications
  → "Draft summary email about findings"
    
Communications: (drafts email)
  → awaits approval from user
```

---

### 3. **Tool Framework** (backend/app/tools/)

#### Tool Manager (manager.py)
- **30+ tools** organized by category
- **Permission system:** Which agents can use which tools
- **Approval gates:** Read free, write/send requires approval
- **Tool execution:** Dispatch to handlers, enforce limits

#### Tool Categories
- **CRM:** crm_read, crm_write (gated)
- **Email:** email_draft, email_send (gated)
- **Calendar:** calendar_read, calendar_write (gated)
- **Web:** web_search, news_fetch
- **Memory:** memory_search, memory_write
- **Contact:** contact_update
- **Analytics:** analytics_read
- **Agent Dispatch:** agent_dispatch

#### Core Tool Handlers (handlers.py)
**Implemented (7):**
- `gmail_read` — Search/read emails
- `gmail_draft` — Draft emails (mock, stub OAuth)
- `calendar_read` — Fetch calendar events (mock)
- `web_search` — Search the web (stub)
- `crm_read` — Read contacts/deals from DB
- `crm_write` — Stage CRM writes for approval (mock)
- `memory_search` — Semantic search over facts (stub pgvector)

**Not yet implemented (stubs):**
- email_send, sms_send, call_answer (waiting for Twilio)
- document_create, analytics_read, agent_definition_write
- All are marked NotImplementedError for clarity

---

### 4. **Orchestrator Dispatch** (backend/app/agents/dispatch.py)

```python
OrchestratorDispatch(org_id, user_id)
  ├─ handle_user_message(message, conversation_id)
  │   └─ _orchestrate(task)  # Agentic loop
  │       ├─ Get memory context
  │       ├─ Call Orchestrator LLM (Haiku for routing)
  │       ├─ For each delegation:
  │       │   └─ _delegate_to_agent(agent_name, task)
  │       └─ Synthesize results (Sonnet) if multiple delegations
  │
  └─ _log_task(task, result, status)
      ├─ Log to actions_log (audit trail)
      └─ Log to usage (billing + tracking)
```

**Key features:**
- **Agents as tools:** LLM sees agents as callable functions
- **Agentic loop:** Keep delegating until task is complete
- **Max hops=3:** Prevent infinite loops
- **Token budget=10k:** Per-task cost control
- **Model call tracking:** Audit what models ran, when, cost

**Task envelope:**
```python
TaskEnvelope:
  task_id: str              # Unique ID
  user_message: str         # Original user input
  hops: int                 # Current loop iteration
  max_hops: int             # Max allowed (3)
  tokens_used: int          # Running total
  token_budget: int         # Max allowed (10k)
  model_calls: List         # [{model, tokens, cost, timestamp}]
```

---

### 5. **Approval Gates**

**Two tiers:**

1. **No approval:** Read operations (crm_read, calendar_read, web_search, memory_search)
2. **Gated (requires approval):** All write/send operations
   - crm_write → creates approval request in actions_log
   - email_send → awaits user approval before sending
   - calendar_write → approval before booking
   - sms_send → approval before sending

**Flow:**
```
Agent calls tool with approval_required=True
  → ToolManager creates approval request
  → Returns approval_id to user
  → User sees action in Approval Queue widget
  → User clicks Approve/Deny
  → Action logged to actions_log with approval_status
  → If approved, actual execution happens (stub for now)
```

---

### 6. **Usage & Cost Tracking**

**Logged per task:**
- Model tier used (Haiku/Sonnet/Opus)
- Tokens consumed (input + output)
- Estimated cost
- All model calls in sequence (for debugging)
- Hops taken, token budget remaining
- Success/error status

**Tables:**
- `actions_log` — Audit trail (who, what, when, approval status)
- `usage` — Billing aggregates (period, tokens, cost)

---

## Architecture Diagram

```
User Message
    ↓
Orchestrator (Haiku)
    ↓
[Intent: "Research?" "Lead qual?" "Content?"]
    ↓
{LLM generates: "delegate_to_research, delegate_to_communications"}
    ↓
Agent Dispatch (implements agent-to-agent protocol)
    ├─→ Research Agent
    │   └─ Tools: web_search, news_fetch, memory_search
    │
    └─→ Communications Agent
        └─ Tools: email_draft, calendar_read (no send without approval)
    ↓
[Gather results]
    ↓
Synthesis (Sonnet)
    ↓
Final Response + Approval Queue entries
    ↓
Log to actions_log + usage
```

---

## What's Testable Now

### End-to-end test (backend/tests/test_pipeline_e2e.py)

```python
test_pipeline_agent_e2e()
  → Webhook lead arrives
  → Orchestrator routes to Pipeline
  → Pipeline calls crm_read (free), crm_write (gated)
  → Approval request created
  → User approves
  → Logged to audit trail
  ✅ Passes

test_approval_gate_for_crm_write()
  → CRM write returns approval_required
  ✅ Passes

test_email_draft_flow()
  → email_draft works (no approval needed)
  → email_send blocked (needs approval)
  ✅ Passes
```

---

## What's NOT implemented yet (stubs)

1. **Agent execution** — `_delegate_to_agent()` returns mock results
   - Real flow: Agent receives task, executes tools, returns results
   - Stub: "delegated" status, needs actual agent inference loop

2. **Semantic memory search** — pgvector queries exist in schema, not wired
   - Real flow: Embedding API → cosine similarity search → results
   - Stub: Returns mock memory entries

3. **OAuth integrations**
   - Gmail read/draft: Needs Google OAuth token retrieval from Vault
   - Calendar read: Needs Google Calendar API setup
   - CRM read/write: Needs Zapier webhook or direct API

4. **Approval workflow endpoints**
   - API to list pending approvals
   - API to approve/deny an action
   - API to execute approved action

5. **Batch API for Research** — Can run Research Agent overnight via Batch API for cost savings
   - Real flow: Submit to Batch API, poll for results
   - Stub: Uses standard API for now

6. **Voice (Layer 5)** — Voice handlers not started

---

## Quick Start for Testing

```bash
# Run the E2E test
cd backend
python -m pytest tests/test_pipeline_e2e.py -v

# Expected output:
# ✅ Lead qualified successfully
# ✅ CRM write gated successfully  
# ✅ Email drafted successfully
```

---

## What Comes Next

### Layer 4 remaining work
1. Implement actual agent execution in `_delegate_to_agent()`
2. Wire OAuth token retrieval from Supabase Vault
3. Build approval workflow API endpoints
4. Implement pgvector semantic search for memory
5. Add Batch API support for scheduled Research

### Layer 5 (Voice)
1. Whisper STT pipeline
2. ElevenLabs TTS
3. Twilio integration
4. Real-time streaming

---

## Key Design Decisions

1. **Agents as tools** — Don't have separate intent detection; let LLM choose which agent via tool use
2. **Haiku for routing** — Most cost-effective for every-turn classification (99% of calls)
3. **Sonnet for synthesis** — Quality matters when stitching multi-agent results
4. **Opus for rare critical work** — Agent Builder config errors are expensive to fix
5. **Max hops=3** — Prevents infinite delegations; agent chain rarely deeper than 3
6. **Token budget=10k** — Typical task ~2k tokens (Haiku routing + 1 Sonnet synthesis)
7. **Approval gates on all writes** — "Read free, write gated" default for safety
8. **Audit logging mandatory** — Every agent action logged to actions_log for compliance

---

## Files

- `backend/app/models.py` — Added AgentRole enums (ORCHESTRATOR, MEMORY_SCRIBE, AGENT_BUILDER)
- `backend/app/agents/orchestrator.py` — 8 agents with full specs
- `backend/app/agents/protocol.py` — Agent message protocol + communication manager
- `backend/app/agents/dispatch.py` — Orchestrator + agentic loop + task tracking
- `backend/app/tools/manager.py` — Tool framework + permissions + approval gates
- `backend/app/tools/handlers.py` — 7 core tool implementations + stubs
- `backend/tests/test_pipeline_e2e.py` — End-to-end test suite

---

**Layer 4 is framework-complete and ready for implementation of the handler stubs.**
