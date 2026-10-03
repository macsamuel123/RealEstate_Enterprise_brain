"""Tool execution framework - manages agent tool permissions and execution."""
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from dataclasses import dataclass
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Categories of tools agents can use."""
    CRM = "crm"              # Read/write CRM data
    EMAIL = "email"           # Draft/send emails
    CALENDAR = "calendar"     # Read/write calendar
    WEB_SEARCH = "web_search" # Search the web
    MEMORY = "memory"         # Read/write memory
    AGENT_DISPATCH = "agent_dispatch"  # Call other agents
    CONTENT = "content"       # Draft documents and content
    ANALYTICS = "analytics"   # Read business metrics
    CONTACT = "contact"       # Manage contacts


@dataclass
class ToolDefinition:
    """Definition of a tool an agent can use."""
    name: str
    category: ToolCategory
    description: str
    requires_approval: bool  # Does this tool action require user approval?
    input_params: Dict[str, str]  # name -> type

    # Which agents are allowed to use this tool (empty = all)
    allowed_agents: List[str] = None


class ToolManager:
    """Manages tool permissions, definitions, and execution."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.tools = self._define_tools()

    def _define_tools(self) -> Dict[str, ToolDefinition]:
        """Define all available tools and their properties."""
        return {
            # CRM Tools
            "crm_read": ToolDefinition(
                name="crm_read",
                category=ToolCategory.CRM,
                description="Read contacts, deals, leads from CRM",
                requires_approval=False,
                input_params={
                    "entity_type": "str",  # contact, deal, lead
                    "filters": "dict",  # SQL-like filters
                    "limit": "int"
                }
            ),
            "crm_write": ToolDefinition(
                name="crm_write",
                category=ToolCategory.CRM,
                description="Create or update CRM records",
                requires_approval=True,  # All CRM writes need approval
                input_params={
                    "entity_type": "str",
                    "action": "str",  # create, update
                    "data": "dict"
                },
                allowed_agents=["lead_qualification", "communications"]
            ),

            # Email Tools
            "email_draft": ToolDefinition(
                name="email_draft",
                category=ToolCategory.EMAIL,
                description="Draft an email (not sent)",
                requires_approval=False,
                input_params={
                    "to": "str",
                    "subject": "str",
                    "body": "str",
                    "template": "str"  # optional
                },
                allowed_agents=["content", "communications", "lead_qualification"]
            ),
            "email_send": ToolDefinition(
                name="email_send",
                category=ToolCategory.EMAIL,
                description="Send an email",
                requires_approval=True,  # Always gate email sending
                input_params={
                    "to": "str",
                    "subject": "str",
                    "body": "str"
                },
                allowed_agents=["communications"]  # Only Comms Agent can send
            ),

            # Calendar Tools
            "calendar_read": ToolDefinition(
                name="calendar_read",
                category=ToolCategory.CALENDAR,
                description="Read calendar events",
                requires_approval=False,
                input_params={
                    "date_range": "tuple",  # (start_date, end_date)
                    "calendar_type": "str"  # outlook, google, etc
                }
            ),
            "calendar_write": ToolDefinition(
                name="calendar_write",
                category=ToolCategory.CALENDAR,
                description="Create or update calendar events",
                requires_approval=True,
                input_params={
                    "title": "str",
                    "start_time": "datetime",
                    "duration_minutes": "int",
                    "attendees": "list",
                    "description": "str"
                },
                allowed_agents=["communications", "concierge"]
            ),

            # Web Search
            "web_search": ToolDefinition(
                name="web_search",
                category=ToolCategory.WEB_SEARCH,
                description="Search the web for information",
                requires_approval=False,
                input_params={
                    "query": "str",
                    "domain_filter": "str"  # optional: only search specific domains
                },
                allowed_agents=["research", "lead_qualification", "concierge"]
            ),
            "news_fetch": ToolDefinition(
                name="news_fetch",
                category=ToolCategory.WEB_SEARCH,
                description="Fetch recent news articles",
                requires_approval=False,
                input_params={
                    "topic": "str",
                    "timeframe": "str",  # last_24h, last_week, last_month
                    "source_filter": "str"  # optional
                },
                allowed_agents=["research"]
            ),

            # Memory Tools
            "memory_recall": ToolDefinition(
                name="memory_recall",
                category=ToolCategory.MEMORY,
                description="Recall facts and decisions from memory",
                requires_approval=False,
                input_params={
                    "query": "str",
                    "category": "str",  # preference, decision, context, relationship, operational
                    "limit": "int"
                }
            ),
            "memory_write": ToolDefinition(
                name="memory_write",
                category=ToolCategory.MEMORY,
                description="Store a new fact or decision in memory",
                requires_approval=False,
                input_params={
                    "fact": "str",
                    "category": "str",
                    "source": "str"  # where this fact came from
                },
                allowed_agents=["memory_scribe"]
            ),

            # Contact Tools
            "contact_update": ToolDefinition(
                name="contact_update",
                category=ToolCategory.CONTACT,
                description="Update contact dossier or profile",
                requires_approval=False,
                input_params={
                    "contact_id": "uuid",
                    "updates": "dict"  # fields to update
                },
                allowed_agents=["memory_scribe", "lead_qualification"]
            ),

            # Agent Dispatch
            "agent_dispatch": ToolDefinition(
                name="agent_dispatch",
                category=ToolCategory.AGENT_DISPATCH,
                description="Route a task to another agent",
                requires_approval=False,
                input_params={
                    "target_agent": "str",  # agent role
                    "task": "str",
                    "context": "dict"
                },
                allowed_agents=["orchestrator"]
            ),

            # Content Tools
            "document_create": ToolDefinition(
                name="document_create",
                category=ToolCategory.CONTENT,
                description="Create a document (blog, report, etc)",
                requires_approval=False,
                input_params={
                    "title": "str",
                    "content": "str",
                    "doc_type": "str"  # blog, report, newsletter
                },
                allowed_agents=["content"]
            ),
            "content_draft": ToolDefinition(
                name="content_draft",
                category=ToolCategory.CONTENT,
                description="Draft content for review",
                requires_approval=False,
                input_params={
                    "content_type": "str",  # blog, social, email, newsletter
                    "topic": "str",
                    "format": "str"  # short, medium, long
                },
                allowed_agents=["content", "communications"]
            ),

            # Analytics
            "analytics_read": ToolDefinition(
                name="analytics_read",
                category=ToolCategory.ANALYTICS,
                description="Read business metrics and analytics",
                requires_approval=False,
                input_params={
                    "metric": "str",  # response_time, conversion_rate, pipeline_value
                    "time_period": "str",  # today, week, month, quarter
                    "filters": "dict"  # optional filters
                },
                allowed_agents=["operational_heartbeat", "research", "lead_qualification"]
            ),
        }

    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name."""
        return self.tools.get(tool_name)

    def can_agent_use_tool(self, agent_role: str, tool_name: str) -> bool:
        """Check if an agent is allowed to use a tool."""
        tool = self.get_tool(tool_name)
        if not tool:
            return False

        # If tool has allowed_agents list, only those can use it
        if tool.allowed_agents:
            return agent_role in tool.allowed_agents

        # Otherwise, all agents can use it
        return True

    async def execute_tool(
        self,
        agent_id: UUID,
        agent_role: str,
        tool_name: str,
        tool_params: Dict[str, Any],
        org_id: UUID,
        user_id: UUID,
        conversation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool with permission checks and approval gates.

        Returns: {
            "status": "success" | "approval_required" | "error",
            "result": {...},
            "approval_id": "uuid" if approval_required,
            "error": "message" if error
        }
        """

        # Check if agent can use this tool
        if not self.can_agent_use_tool(agent_role, tool_name):
            logger.warning(f"Agent {agent_role} not allowed to use {tool_name}")
            return {
                "status": "error",
                "error": f"Agent {agent_role} is not permitted to use tool {tool_name}"
            }

        tool = self.get_tool(tool_name)

        # Check if approval is required
        if tool.requires_approval:
            # Create approval request
            approval_id = await self._create_approval_request(
                agent_id=agent_id,
                tool_name=tool_name,
                tool_params=tool_params,
                org_id=org_id,
                user_id=user_id,
                conversation_id=conversation_id
            )

            return {
                "status": "approval_required",
                "approval_id": str(approval_id),
                "message": f"Action requires approval: {tool.description}"
            }

        # Execute tool (stub - will implement per-tool)
        result = await self._execute_tool_internal(
            tool_name=tool_name,
            tool_params=tool_params,
            org_id=org_id,
            user_id=user_id
        )

        # Log the action
        await self._log_tool_execution(
            agent_id=agent_id,
            tool_name=tool_name,
            tool_params=tool_params,
            result=result,
            org_id=org_id,
            user_id=user_id,
            conversation_id=conversation_id
        )

        return {
            "status": "success",
            "result": result
        }

    async def _create_approval_request(
        self,
        agent_id: UUID,
        tool_name: str,
        tool_params: Dict[str, Any],
        org_id: UUID,
        user_id: UUID,
        conversation_id: Optional[UUID]
    ) -> UUID:
        """Create an approval request for a tool action."""
        # TODO: Insert into actions_log table with approval_status=PENDING
        # Return the approval_id
        pass

    async def _execute_tool_internal(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        org_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Execute the actual tool via handler."""
        from app.tools.handlers import ToolHandlers

        handlers = ToolHandlers(self.supabase)

        try:
            result = await handlers.execute(
                tool_name=tool_name,
                org_id=org_id,
                user_id=user_id,
                **tool_params
            )
            return result
        except NotImplementedError as e:
            logger.warning(f"Tool not implemented: {tool_name}")
            return {
                "status": "not_implemented",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name}: {e}")
            raise

    async def _log_tool_execution(
        self,
        agent_id: UUID,
        tool_name: str,
        tool_params: Dict[str, Any],
        result: Dict[str, Any],
        org_id: UUID,
        user_id: UUID,
        conversation_id: Optional[UUID]
    ):
        """Log tool execution to audit trail."""
        # TODO: Insert into actions_log table
        pass
