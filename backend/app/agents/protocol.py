"""Agent-to-Agent Protocol - defines how agents communicate and delegate tasks."""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import UUID
import json

class AgentMessageType(str, Enum):
    """Types of messages agents can send to each other."""
    REQUEST = "request"  # Agent A asks Agent B to do something
    RESULT = "result"    # Agent B returns results to Agent A
    DELEGATE = "delegate"  # Orchestrator routes task to an agent
    ERROR = "error"      # Agent encountered error


@dataclass
class AgentMessage:
    """Message passed between agents in the protocol."""
    message_type: AgentMessageType
    from_agent_role: str  # e.g. "orchestrator", "research", "lead_qualification"
    to_agent_role: str

    task_description: str  # What needs to be done
    context: Dict[str, Any]  # Relevant context (contact_id, deal_id, etc)

    # For delegated tasks
    conversation_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    org_id: Optional[UUID] = None

    # For results
    status: str = "pending"  # pending, success, error
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage/transmission."""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        if self.conversation_id:
            data["conversation_id"] = str(self.conversation_id)
        if self.user_id:
            data["user_id"] = str(self.user_id)
        if self.org_id:
            data["org_id"] = str(self.org_id)
        return data


class AgentCommunicationManager:
    """Manages agent-to-agent communication and delegation."""

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def send_request(
        self,
        from_agent_role: str,
        to_agent_role: str,
        task_description: str,
        context: Dict[str, Any],
        org_id: UUID,
        conversation_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> AgentMessage:
        """
        One agent requests another agent to do something.

        Example:
        - Orchestrator asks Research Agent to "Research competitor X"
        - Lead Qualification Agent asks Communications Agent to "Draft intro email"
        """

        message = AgentMessage(
            message_type=AgentMessageType.REQUEST,
            from_agent_role=from_agent_role,
            to_agent_role=to_agent_role,
            task_description=task_description,
            context=context,
            org_id=org_id,
            conversation_id=conversation_id,
            user_id=user_id,
            status="pending"
        )

        # Store request in database for audit trail
        await self._store_message(message)

        return message

    async def send_result(
        self,
        from_agent_role: str,
        to_agent_role: str,
        task_description: str,
        result: Dict[str, Any],
        org_id: UUID,
        conversation_id: Optional[UUID] = None,
        error_message: Optional[str] = None
    ) -> AgentMessage:
        """
        Agent returns result to requesting agent.

        Example:
        - Research Agent returns findings about competitor X
        - Communications Agent returns drafted email for approval
        """

        message = AgentMessage(
            message_type=AgentMessageType.RESULT,
            from_agent_role=from_agent_role,
            to_agent_role=to_agent_role,
            task_description=task_description,
            context={},
            org_id=org_id,
            conversation_id=conversation_id,
            status="success" if not error_message else "error",
            result=result,
            error_message=error_message
        )

        await self._store_message(message)
        return message

    async def delegate_to_agent(
        self,
        agent_role: str,
        task_description: str,
        context: Dict[str, Any],
        org_id: UUID,
        user_id: UUID,
        conversation_id: Optional[UUID] = None
    ) -> AgentMessage:
        """
        Orchestrator delegates a task to a specialist agent.

        Example:
        - Route "Research market in Calgary" to Research Agent
        - Route "Draft a blog post about mortgages" to Content Agent
        """

        message = AgentMessage(
            message_type=AgentMessageType.DELEGATE,
            from_agent_role="orchestrator",
            to_agent_role=agent_role,
            task_description=task_description,
            context=context,
            org_id=org_id,
            user_id=user_id,
            conversation_id=conversation_id,
            status="pending"
        )

        await self._store_message(message)
        return message

    async def _store_message(self, message: AgentMessage):
        """Store agent message in database for audit trail."""
        # TODO: Create agent_messages table in schema to log all inter-agent communication
        # This ensures we can audit and debug agent workflows
        pass

    @staticmethod
    def build_context(
        contact_id: Optional[UUID] = None,
        deal_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Helper to build context dict for agent requests."""
        context = {}
        if contact_id:
            context["contact_id"] = str(contact_id)
        if deal_id:
            context["deal_id"] = str(deal_id)
        if conversation_id:
            context["conversation_id"] = str(conversation_id)
        if additional_data:
            context.update(additional_data)
        return context
