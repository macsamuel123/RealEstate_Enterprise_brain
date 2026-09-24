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
        Returns the agent's response.
        """

        # Route event to agent(s)
        if event_type == "inbound_lead":
            agent_role = "lead_qualification"
        elif event_type == "scheduled_brief":
            agent_role = "research"
        elif event_type == "content_request":
            agent_role = "content"
        elif event_type == "user_message":
            # Determine agent from conversation or message intent
            agent_role = await self._detect_intent(event_data.get("message", ""))
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
        # TODO: Use simple keyword matching or LLM to detect intent
        # For now, default to chat/research
        return "research"

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
    """Create default set of agents for a new organization."""
    supabase = get_supabase()

    default_agents = [
        {
            "org_id": str(org_id),
            "name": "Research Agent",
            "role": "research",
            "description": "Researches market trends, competitor activity, and macro news",
            "system_prompt": """You are a research agent for a real estate business. Your job is to:
1. Monitor market trends and competitor activity
2. Track relevant news and policy changes
3. Synthesize information into actionable insights
4. Report findings proactively

Be concise and fact-based. Always cite sources.""",
            "permitted_tools": ["web_search", "news_fetch", "calendar_read"],
            "is_system_provided": True
        },
        {
            "org_id": str(org_id),
            "name": "Lead Qualification Agent",
            "role": "lead_qualification",
            "description": "Qualifies inbound leads and routes them appropriately",
            "system_prompt": """You are a lead qualification agent. Your job is to:
1. Score leads against qualification criteria
2. Research lead background and intent
3. Route leads to appropriate team members
4. Log all decisions in the CRM

Be efficient and accurate.""",
            "permitted_tools": ["crm_read", "web_search", "email_draft"],
            "is_system_provided": True
        },
        {
            "org_id": str(org_id),
            "name": "Content Agent",
            "role": "content",
            "description": "Generates blogs, social posts, newsletters, and reports",
            "system_prompt": """You are a content creation agent. Your job is to:
1. Write blog posts and articles
2. Create social media content
3. Draft newsletters and client reports
4. Maintain consistent brand voice

Write engaging, professional content.""",
            "permitted_tools": ["document_create", "social_draft", "email_draft"],
            "is_system_provided": True
        },
        {
            "org_id": str(org_id),
            "name": "Communications Agent",
            "role": "communications",
            "description": "Handles calls, emails, SMS, and scheduling",
            "system_prompt": """You are a communications agent. Your job is to:
1. Draft and send emails
2. Manage calendar and scheduling
3. Send SMS/WhatsApp messages
4. Answer phone calls and qualify callers

Be professional and efficient.""",
            "permitted_tools": ["email_send", "calendar_write", "sms_send", "call_answer"],
            "is_system_provided": True
        },
        {
            "org_id": str(org_id),
            "name": "Operational Heartbeat Agent",
            "role": "operational_heartbeat",
            "description": "Monitors business health and flags anomalies",
            "system_prompt": """You are an operational heartbeat agent. Your job is to:
1. Monitor key business metrics (response time, conversion rate, pipeline)
2. Detect anomalies and trends
3. Alert the user proactively when things go wrong
4. Suggest operational improvements

Be objective and data-driven.""",
            "permitted_tools": ["crm_read", "analytics_read", "alert_send"],
            "is_system_provided": True
        },
        {
            "org_id": str(org_id),
            "name": "Concierge Agent",
            "role": "concierge",
            "description": "Personal assistant for restaurants, reminders, and admin",
            "system_prompt": """You are a personal concierge agent. Your job is to:
1. Research and book restaurants
2. Remember client preferences and birthdays
3. Handle personal admin tasks
4. Proactively remind the user of important dates

Be thoughtful and attentive to detail.""",
            "permitted_tools": ["web_search", "calendar_write", "email_send"],
            "is_system_provided": True
        }
    ]

    for agent_def in default_agents:
        supabase.table("agent").insert(agent_def).execute()

    logger.info(f"Created {len(default_agents)} default agents for org {org_id}")
