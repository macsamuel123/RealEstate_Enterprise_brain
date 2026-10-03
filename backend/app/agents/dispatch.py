"""Orchestrator dispatch - treats agents as tools, implements agentic loop."""
from typing import Optional, Dict, Any, List
from uuid import UUID
from dataclasses import dataclass, field
import logging
import json
from datetime import datetime, date

from app.models import ActionType, ApprovalStatus
from app.database import get_supabase
from app.llm.router import LLMRouter, LLMProvider
from app.agents.protocol import AgentCommunicationManager, AgentMessageType
from app.tools.manager import ToolManager

logger = logging.getLogger(__name__)


@dataclass
class TaskEnvelope:
    """Wraps a task being executed by the orchestrator."""
    task_id: str
    user_message: str
    org_id: UUID
    user_id: UUID
    conversation_id: UUID

    # Tracking
    hops: int = 0
    max_hops: int = 3
    tokens_used: int = 0
    token_budget: int = 10000
    model_calls: List[Dict[str, Any]] = field(default_factory=list)

    def can_hop(self) -> bool:
        """Check if we can make another agent call."""
        return self.hops < self.max_hops and self.tokens_used < self.token_budget

    def add_model_call(self, model: str, tokens: int, cost: float):
        """Log a model call."""
        if not self.model_calls:
            self.model_calls = []
        self.model_calls.append({
            "model": model,
            "tokens": tokens,
            "cost": cost,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.tokens_used += tokens


class OrchestratorDispatch:
    """Orchestrator that treats agents as callable tools."""

    def __init__(self, org_id: UUID, user_id: UUID):
        self.org_id = org_id
        self.user_id = user_id
        self.supabase = get_supabase()
        self.tool_manager = ToolManager(self.supabase)
        self.comm_manager = AgentCommunicationManager(self.supabase)

        # LLM for routing
        self.router = LLMRouter(
            primary=LLMProvider.ANTHROPIC,
            model="claude-haiku-4-5-20251001",  # Haiku for routing
            temperature=0.3,
            max_tokens=500
        )

    async def handle_user_message(
        self,
        message: str,
        conversation_id: UUID
    ) -> Dict[str, Any]:
        """
        Main entry point: user says something, orchestrator decides what to do.

        The Orchestrator is an LLM that:
        1. Understands the user's intent
        2. Has access to "delegate_to_<agent>" tools
        3. Calls appropriate agents
        4. Synthesizes results

        Flow:
        - Orchestrator reads user message
        - Calls LLM with available tools (agents)
        - LLM decides: delegate to Research? Lead Qual? Ask clarification?
        - For each delegation, call that agent
        - Gather results
        - Synthesize with Sonnet for final answer
        """

        # Create task envelope
        task = TaskEnvelope(
            task_id=f"task_{datetime.utcnow().timestamp()}",
            user_message=message,
            org_id=self.org_id,
            user_id=self.user_id,
            conversation_id=conversation_id
        )

        try:
            # Agentic loop: keep delegating until task is complete
            result = await self._orchestrate(task)

            # Log final result
            await self._log_task(task, result, "success")

            return result

        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            await self._log_task(task, {"error": str(e)}, "error")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _orchestrate(self, task: TaskEnvelope) -> Dict[str, Any]:
        """Agentic loop: delegate to agents, gather results, synthesize."""

        # Build the system prompt for Orchestrator
        system_prompt = """You are the Orchestrator — Shawn's Chief of Staff AI.

Your job is to:
1. Understand what Shawn is asking
2. Decide which agent(s) should help
3. Ask clarifying questions if needed
4. Delegate tasks to specialist agents
5. Synthesize their results into a clear response

Available agents you can delegate to:
- delegate_to_research: Market research, competitor analysis, news
- delegate_to_lead_qualification: Qualify leads, score prospects
- delegate_to_content: Write blogs, social posts, newsletters
- delegate_to_communications: Draft emails, schedule calls
- delegate_to_memory_search: Find relevant facts from past conversations

When delegating, provide clear context and what you need back.
Ask clarifying questions if the request is ambiguous.
Never send emails or make CRM changes without explicit approval.

Return your response in JSON:
{
  "understanding": "What you think Shawn is asking for",
  "actions": [
    {
      "type": "delegate" | "clarification" | "direct_response",
      "target": "research | lead_qualification | content | communications | memory_search",
      "task": "What you're asking that agent to do"
    }
  ],
  "response": "Final response to Shawn (only if no delegation needed)"
}"""

        # Get memory context
        memory_context = await self._get_memory_context(task)

        # Call Orchestrator (Haiku for routing)
        orchestrator_prompt = f"""User message: {task.user_message}

Recent context:
{json.dumps(memory_context, indent=2)}

What should we do?"""

        routing_response = await self.router.complete(
            system_prompt=system_prompt,
            user_message=orchestrator_prompt
        )

        # Parse routing response
        try:
            routing = json.loads(routing_response)
        except json.JSONDecodeError:
            # If not valid JSON, ask for clarification
            routing = {
                "understanding": routing_response,
                "actions": [{
                    "type": "clarification",
                    "task": "Could you clarify what you need?"
                }],
                "response": routing_response
            }

        # Execute delegations
        delegation_results = []
        for action in routing.get("actions", []):
            if not task.can_hop():
                logger.warning(f"Task {task.task_id} hit hop/token limit")
                break

            if action["type"] == "delegate":
                result = await self._delegate_to_agent(
                    task=task,
                    agent_name=action.get("target"),
                    agent_task=action.get("task")
                )
                delegation_results.append({
                    "agent": action.get("target"),
                    "task": action.get("task"),
                    "result": result
                })

        # If direct response, return it
        if routing.get("response"):
            return {
                "status": "success",
                "response": routing["response"],
                "delegations": delegation_results
            }

        # Otherwise synthesize delegation results
        if delegation_results:
            synthesis_prompt = f"""User asked: {task.user_message}

Results from agents:
{json.dumps(delegation_results, indent=2)}

Synthesize this into a clear response for Shawn."""

            # Use Sonnet for synthesis (better quality for multi-step results)
            synthesizer = LLMRouter(
                primary=LLMProvider.ANTHROPIC,
                model="claude-sonnet-5",
                temperature=0.5,
                max_tokens=1000
            )

            synthesis = await synthesizer.complete(
                system_prompt="You are synthesizing agent results into a clear response.",
                user_message=synthesis_prompt
            )

            return {
                "status": "success",
                "response": synthesis,
                "delegations": delegation_results
            }

        # No delegations, no direct response = unclear
        return {
            "status": "clarification_needed",
            "response": "I'm not sure what you're asking for. Could you clarify?"
        }

    async def _delegate_to_agent(
        self,
        task: TaskEnvelope,
        agent_name: str,
        agent_task: str
    ) -> Dict[str, Any]:
        """Delegate a task to a specialist agent."""

        task.hops += 1
        logger.info(f"Task {task.task_id} hop {task.hops}: delegating to {agent_name}")

        # Map agent names to roles
        agent_role_map = {
            "research": "research",
            "lead_qualification": "lead_qualification",
            "content": "content",
            "communications": "communications",
            "memory_search": "memory"  # Special case: not an agent, a tool
        }

        agent_role = agent_role_map.get(agent_name)
        if not agent_role:
            return {"error": f"Unknown agent: {agent_name}"}

        # Special handling for memory_search (it's a tool, not an agent)
        if agent_name == "memory_search":
            result = await self.tool_manager.execute_tool(
                agent_id=None,
                agent_role="orchestrator",
                tool_name="memory_search",
                tool_params={"query": agent_task, "limit": 5},
                org_id=task.org_id,
                user_id=task.user_id,
                conversation_id=task.conversation_id
            )
            return result

        # For other agents: send via protocol
        message = await self.comm_manager.delegate_to_agent(
            agent_role=agent_role,
            task_description=agent_task,
            context={"original_message": task.user_message},
            org_id=task.org_id,
            user_id=task.user_id,
            conversation_id=task.conversation_id
        )

        # TODO: Actually execute the agent
        # For now, return mock result
        return {
            "status": "delegated",
            "agent": agent_name,
            "task": agent_task,
            "message_id": str(message.message_id) if hasattr(message, 'message_id') else None
        }

    async def _get_memory_context(self, task: TaskEnvelope) -> Dict[str, Any]:
        """Get relevant memory context for the task."""
        # TODO: Implement semantic search over memory
        # For now, return empty
        return {}

    async def _log_task(
        self,
        task: TaskEnvelope,
        result: Dict[str, Any],
        status: str
    ):
        """Log task execution to usage and actions_log."""
        try:
            # Calculate cost (rough estimate)
            cost_per_1k = {
                "claude-opus-5-5": 0.015,
                "claude-sonnet-5": 0.003,
                "claude-haiku-4-5-20251001": 0.0008
            }
            total_cost = sum(
                cost_per_1k.get(call["model"], 0.001) * (call["tokens"] / 1000)
                for call in (task.model_calls or [])
            )

            # Log to actions_log
            self.supabase.table("actions_log").insert({
                "org_id": str(task.org_id),
                "user_id": str(task.user_id),
                "action_type": ActionType.AGENT_DISPATCH.value,
                "status": status,
                "input_data": {"message": task.user_message},
                "output_data": result,
                "metadata": {
                    "task_id": task.task_id,
                    "hops": task.hops,
                    "tokens_used": task.tokens_used,
                    "model_calls": task.model_calls or []
                }
            }).execute()

            # Log to usage (for billing)
            today = date.today()
            self.supabase.table("usage").upsert({
                "org_id": str(task.org_id),
                "period_start": today,
                "period_end": today,
                "model_tokens_input": task.tokens_used,
                "model_tokens_output": 0,  # TODO: track output separately
            }, on_conflict=["org_id", "period_start", "period_end"]).execute()

        except Exception as e:
            logger.error(f"Failed to log task: {e}")
