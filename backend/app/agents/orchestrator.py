"""Agent orchestrator - routes tasks to appropriate agents."""
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging
from datetime import datetime

from app.models import Agent, Conversation, ActionsLog, ActionType, ApprovalStatus
from app.database import get_supabase
from app.llm.router import get_model_for_task

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Routes tasks to the appropriate agent."""

    def __init__(self, org_id: UUID, user_id: UUID):
        self.org_id = org_id
        self.user_id = user_id
        self.supabase = get_supabase()
        self.agents_cache: Dict[str, Agent] = {}

    async def get_standard_agents(self) -> Dict[str, Agent]:
        """Get or create standard agents for this org."""
        if self.agents_cache:
            return self.agents_cache

        # Fetch from database
        response = self.supabase.table("agent").select("*").eq("org_id", str(self.org_id)).execute()
        agents = response.data or []

        for agent_data in agents:
            # TODO: Deserialize to Agent model
            pass

        return self.agents_cache

    async def dispatch_to_agent(
        self,
        event_type: str,  # "inbound_lead", "scheduled_brief", "user_message", etc
        event_data: Dict[str, Any],
        conversation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Dispatch an event to the appropriate agent.
        For user messages, use conversational agent (Claude decides what to do).
        Returns the agent's response.
        """

        # For conversational user messages, use the conversational agent
        if event_type == "user_message":
            from app.agents.conversational import ConversationalAgent

            agent = ConversationalAgent(org_id=str(self.org_id), user_id=str(self.user_id))
            message = event_data.get("message", "")

            try:
                response = await agent.chat(message)
                return {
                    "status": "success",
                    "response": response,
                    "conversation_id": str(conversation_id) if conversation_id else None
                }
            except Exception as e:
                logger.error(f"Conversational agent error: {e}")
                return {
                    "status": "error",
                    "error": str(e)
                }

        # Route other event types to specific agents
        if event_type == "inbound_lead":
            agent_role = "lead_qualification"
        elif event_type == "scheduled_brief":
            agent_role = "research"
        elif event_type == "content_request":
            agent_role = "content"
        else:
            agent_role = "research"  # Default

        # Get agent
        agent = await self._get_agent_by_role(agent_role)
        if not agent:
            logger.error(f"No agent found for role: {agent_role}")
            return {"error": "No agent available for this task"}

        # Execute agent
        result = await self._execute_agent(
            agent=agent,
            event_type=event_type,
            event_data=event_data,
            conversation_id=conversation_id
        )

        return result

    async def _get_agent_by_role(self, role: str) -> Optional[Agent]:
        """Get an agent by role, falling back to system-provided if custom not found."""
        agents = await self.get_standard_agents()

        # Try to find agent with this role in this org
        for agent in agents.values():
            if agent.role == role:  # TODO: proper enum comparison
                return agent

        # TODO: Fall back to system-provided default
        return None

    async def _execute_agent(
        self,
        agent: Agent,
        event_type: str,
        event_data: Dict[str, Any],
        conversation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Execute an agent with the given input."""

        # Create conversation if needed
        if not conversation_id:
            conv_response = self.supabase.table("conversation").insert({
                "org_id": str(self.org_id),
                "user_id": str(self.user_id),
                "agent_id": str(agent.id),
                "channel": "chat",
                "title": event_data.get("title", f"Task: {event_type}")
            }).execute()
            conversation_id = conv_response.data[0]["id"]

        # Log action
        await self._log_action(
            agent_id=agent.id,
            action_type=ActionType.AGENT_DISPATCH,
            input_data=event_data,
            approval_required=agent.requires_approval
        )

        # Call LLM via agent's system prompt
        try:
            # TODO: Implement LLM call
            # model = get_model_for_task(agent.model, agent.temperature, agent.max_tokens)
            # response = await model.complete(system_prompt=agent.system_prompt, user_message=...)

            response = {
                "status": "success",
                "agent_id": str(agent.id),
                "response": "Agent execution placeholder",
                "conversation_id": str(conversation_id)
            }

            # Log success
            await self._log_action(
                agent_id=agent.id,
                action_type=ActionType.AGENT_DISPATCH,
                output_data=response,
                status="success"
            )

        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            # Log error
            await self._log_action(
                agent_id=agent.id,
                action_type=ActionType.AGENT_DISPATCH,
                status="error",
                error_message=str(e)
            )

            return {
                "status": "error",
                "error": str(e)
            }

        return response

    async def _detect_intent(self, message: str) -> str:
        """Detect user intent from message."""
        from app.agents.intent import detect_intent

        intent, _ = detect_intent(message)

        intent_to_role = {
            "brief_me": "orchestrator_brief",
            "who_am_i_meeting": "orchestrator_calendar",
            "follow_up_recruits": "communications",
            "book_coffee": "orchestrator_calendar",
            "what_needs_attention": "orchestrator_heartbeat",
            "unclear": "orchestrator",
        }

        return intent_to_role.get(intent.value, "research")

    async def _log_action(
        self,
        agent_id: Optional[UUID],
        action_type: ActionType,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        approval_required: bool = False
    ):
        """Log an action to the audit trail."""

        self.supabase.table("actions_log").insert({
            "org_id": str(self.org_id),
            "user_id": str(self.user_id),
            "agent_id": str(agent_id) if agent_id else None,
            "action_type": action_type.value,
            "input_data": input_data,
            "output_data": output_data,
            "status": status,
            "error_message": error_message,
            "approval_required": approval_required,
            "approval_status": ApprovalStatus.PENDING.value if approval_required else ApprovalStatus.APPROVED.value
        }).execute()

async def create_default_agents(org_id: UUID):
    """Create all 8 standard agents for a new organization."""
    supabase = get_supabase()

    default_agents = [
        {
            "org_id": str(org_id),
            "name": "Orchestrator (Chief of Staff)",
            "role": "orchestrator",
            "description": "The single persona Shawn talks to. Routes tasks, clarifies intent, synthesizes results, runs onboarding and evening check-in",
            "system_prompt": """You are the Orchestrator — Shawn's Chief of Staff AI. Your role is to:
1. Listen to Shawn's requests and understand intent
2. Route tasks to the right specialist agent or handle directly
3. Ask clarifying questions when needed (CRM data, context, preferences)
4. Synthesize results from multiple agents into clear summaries
5. Run onboarding flows and evening check-ins

Use a professional, concise tone. Always ask for clarification if intent is ambiguous.
Never send emails or make changes without explicit approval.""",
            "model": "claude-haiku-4-5-20251001",
            "temperature": 0.5,
            "max_tokens": 1000,
            "permitted_tools": ["agent_dispatch", "memory_recall"],
            "requires_approval": False,
            "is_system_provided": True,
            "metadata": {
                "model_for_routing": "claude-haiku-4-5-20251001",
                "model_for_synthesis": "claude-sonnet-5",
                "note": "Routing (classification) uses Haiku; synthesis (multi-agent results) uses Sonnet. High-volume agent."
            }
        },
        {
            "org_id": str(org_id),
            "name": "Memory Scribe",
            "role": "memory_scribe",
            "description": "Extracts facts, decisions, and commitments from conversations. Maintains contact dossiers and pre-call briefings",
            "system_prompt": """You are the Memory Scribe. After each conversation, your job is to:
1. Extract factual information (dates, names, preferences, decisions)
2. Identify commitments and follow-ups
3. Update contact profiles and dossiers
4. Build pre-call briefings from past interactions
5. Identify patterns and recurring themes

Be precise and only extract explicitly stated facts, not inferred information.
Work async in the background — no user-facing output.""",
            "model": "claude-haiku-4-5-20251001",
            "temperature": 0.3,
            "max_tokens": 500,
            "permitted_tools": ["memory_write", "contact_update"],
            "requires_approval": False,
            "should_run_on_schedule": True,
            "schedule_cron": "*/30 * * * *",
            "is_system_provided": True
        },
        {
            "org_id": str(org_id),
            "name": "Research Agent",
            "role": "research",
            "description": "Researches market trends, competitor activity, local market data, and macro news. Feeds the morning brief",
            "system_prompt": """You are the Research Agent. Your job is to:
1. Research market trends and competitor activity (Streams 1–3: macro, local, competitors)
2. Track relevant news, policy changes, and industry shifts
3. Synthesize information into actionable insights for real estate
4. Cite all sources clearly
5. Flag opportunities and threats

Use the Batch API for overnight research runs. Be fact-based and concise.""",
            "model": "claude-sonnet-5",
            "temperature": 0.6,
            "max_tokens": 1500,
            "permitted_tools": ["web_search", "news_fetch", "calendar_read"],
            "requires_approval": False,
            "should_run_on_schedule": True,
            "schedule_cron": "0 22 * * *",
            "is_system_provided": True,
            "metadata": {
                "batch_api": True,
                "batch_cron": "0 22 * * *",
                "note": "Runs overnight via Batch API for cost savings. Public data tasks can use budget tier."
            }
        },
        {
            "org_id": str(org_id),
            "name": "Pipeline Agent (Lead Qualification)",
            "role": "lead_qualification",
            "description": "Qualifies inbound leads, sequences follow-ups, manages recruiting pipeline, and generates pre-call briefings",
            "system_prompt": """You are the Pipeline Agent. Your job is to:
1. Score and qualify inbound leads against Shawn's criteria
2. Sequence follow-up actions intelligently
3. Track recruiting pipeline opportunities
4. Generate pre-call briefings from contact history and memory
5. Log decisions in the CRM

Be thorough but efficient. Read from CRM freely; write operations require approval.""",
            "model": "claude-sonnet-5",
            "temperature": 0.5,
            "max_tokens": 1200,
            "permitted_tools": ["crm_read", "crm_write", "web_search", "memory_recall"],
            "requires_approval": True,
            "is_system_provided": True,
            "metadata": {
                "note": "Structured work: lead scoring against defined criteria. Sonnet handles classification well."
            }
        },
        {
            "org_id": str(org_id),
            "name": "Content Agent",
            "role": "content",
            "description": "Creates blogs, social posts, newsletters, and reports in Shawn's learned voice",
            "system_prompt": """You are the Content Agent. Your job is to:
1. Write blog posts and articles on real estate topics
2. Create engaging social media content (LinkedIn, Instagram)
3. Draft newsletters and client reports
4. Maintain consistent brand voice and style
5. Always tailor content to Shawn's market and audience

Draft content only — no publishing without approval. Study Shawn's past content for voice/style.""",
            "model": "claude-sonnet-5",
            "temperature": 0.7,
            "max_tokens": 2000,
            "permitted_tools": ["document_create", "content_draft"],
            "requires_approval": True,
            "is_system_provided": True,
            "metadata": {
                "fallback_to_opus_if": "voice_style_eval fails",
                "note": "Sonnet writes well. Use Opus only if evals show brand voice mismatch."
            }
        },
        {
            "org_id": str(org_id),
            "name": "Operational Heartbeat Agent",
            "role": "operational_heartbeat",
            "description": "Monitors business vital signs (response time, conversion rate, pipeline). Detects anomalies and suggests fixes",
            "system_prompt": """You are the Heartbeat Agent. Your job is to:
1. Monitor key metrics: System Integrity, Response Time, Pipeline Value, Anomalies
2. Detect statistical anomalies (z-scores > 2.5, trend breaks)
3. Calculate vital signs: response time, lead-to-close rate, deal velocity
4. Narrate findings and suggest operational improvements
5. Flag urgent issues for immediate attention

Be data-driven. Use SQL and simple statistics; avoid speculative commentary.""",
            "model": "claude-haiku-4-5-20251001",
            "temperature": 0.3,
            "max_tokens": 800,
            "permitted_tools": ["crm_read", "analytics_read"],
            "requires_approval": False,
            "should_run_on_schedule": True,
            "schedule_cron": "0 8 * * *",
            "is_system_provided": True
        },
        {
            "org_id": str(org_id),
            "name": "Communications Agent",
            "role": "communications",
            "description": "Handles email, SMS, calls, scheduling, and concierge bookings. The only agent that can send",
            "system_prompt": """You are the Communications Agent. Your job is to:
1. Draft and send emails (always gated, requires approval)
2. Schedule calendar events and manage availability
3. Send SMS/WhatsApp messages (always gated)
4. Answer inbound phone calls and qualify callers
5. Book reservations and handle concierge requests

Be professional and efficient. All send operations require explicit approval.
On live calls, use fast inference; pre-call use full reasoning.""",
            "model": "claude-sonnet-5",
            "temperature": 0.5,
            "max_tokens": 800,
            "permitted_tools": ["email_draft", "email_send", "calendar_write", "sms_send", "call_answer"],
            "requires_approval": True,
            "is_system_provided": True,
            "metadata": {
                "model_for_drafts": "claude-sonnet-5",
                "model_for_live_calls": "claude-haiku-4-5-20251001",
                "note": "Drafts use Sonnet for quality. Live calls use Haiku for <500ms latency. Speed > quality on calls."
            }
        },
        {
            "org_id": str(org_id),
            "name": "Agent Builder",
            "role": "agent_builder",
            "description": "Converts requests like 'watch my competitors' listings' into new agent configurations (prompt, tools, schedule)",
            "system_prompt": """You are the Agent Builder. Your job is to:
1. Listen to user requests for new automated behaviors
2. Convert them into agent configurations (prompt, tool allowlist, schedule)
3. Define what data the agent reads and what it can change
4. Never generate code — only configuration
5. Restrict toolsets to minimum necessary

Example: 'watch my competitors' listings' → New Research Agent with crm_read + web_search, runs daily at 8am.
Always ask clarifying questions about frequency, scope, and approval gates.""",
            "model": "claude-opus-5-5",
            "temperature": 0.5,
            "max_tokens": 1000,
            "permitted_tools": ["agent_definition_write"],
            "requires_approval": True,
            "is_system_provided": True
        }
    ]

    for agent_def in default_agents:
        supabase.table("agent").insert(agent_def).execute()

    logger.info(f"Created {len(default_agents)} standard agents for org {org_id}")
