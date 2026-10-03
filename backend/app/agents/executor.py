"""Agent executor - real agentic loop with step cap."""
from typing import Dict, Any, Optional
from uuid import UUID
import logging
from datetime import datetime

from app.models import Agent, ActionType, ApprovalStatus
from app.database import get_supabase
from app.llm.router import LLMRouter, LLMProvider
from app.tools.manager import ToolManager

logger = logging.getLogger(__name__)


class AgentExecutor:
    """Execute an agent with agentic loop (max 8 steps per agent)."""

    def __init__(
        self,
        agent: Agent,
        org_id: UUID,
        user_id: UUID,
        conversation_id: UUID,
        token_budget: int = 5000
    ):
        self.agent = agent
        self.org_id = org_id
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.token_budget = token_budget
        self.supabase = get_supabase()
        self.tool_manager = ToolManager(self.supabase)

        # LLM for agent
        self.llm = LLMRouter(
            primary=LLMProvider.ANTHROPIC,
            model=agent.model,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens
        )

        # Tracking
        self.steps = 0
        self.max_steps = 8
        self.tokens_used = 0
        self.tool_calls = []

    async def run(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute agent with agentic loop.

        Loop:
        1. Agent reads task + context
        2. Agent decides: use a tool OR return result
        3. If tool: execute with approval gate
        4. If result: done
        5. Repeat (max 8 steps)
        """

        context = context or {}
        messages = []

        # Build system prompt with available tools
        available_tools = self.agent.permitted_tools
        tools_str = "\n".join([f"- {t}" for t in available_tools])

        system_prompt = f"""{self.agent.system_prompt}

AVAILABLE TOOLS:
{tools_str}

To use a tool, respond with JSON:
{{"tool": "tool_name", "params": {{...}}, "reasoning": "why"}}

To return your result, respond with JSON:
{{"result": "your response", "summary": "brief summary"}}"""

        logger.info(f"Agent {self.agent.role} starting: {task_description}")

        while self.steps < self.max_steps:
            self.steps += 1

            if self.tokens_used > self.token_budget:
                logger.warning(f"Agent hit token budget ({self.tokens_used}/{self.token_budget})")
                break

            # Add task to messages (first iteration only)
            if self.steps == 1:
                messages.append({
                    "role": "user",
                    "content": f"Task: {task_description}\n\nContext: {str(context)}"
                })

            # Get agent decision
            response = await self.llm.complete(
                system_prompt=system_prompt,
                user_message="What's your next step?",
                messages=messages
            )

            self.tokens_used += len(response.split()) * 1.3  # Rough estimate

            # Parse response
            try:
                import json
                decision = json.loads(response)
            except json.JSONDecodeError:
                logger.warning(f"Agent returned non-JSON: {response[:100]}")
                return {
                    "status": "error",
                    "error": "Agent response not JSON",
                    "steps": self.steps,
                    "tokens_used": self.tokens_used
                }

            # Handle result
            if "result" in decision:
                logger.info(f"Agent {self.agent.role} completed in {self.steps} steps")
                return {
                    "status": "success",
                    "result": decision["result"],
                    "summary": decision.get("summary", ""),
                    "steps": self.steps,
                    "tokens_used": self.tokens_used,
                    "tool_calls": self.tool_calls
                }

            # Handle tool call
            if "tool" in decision:
                tool_name = decision["tool"]
                tool_params = decision.get("params", {})

                if tool_name not in available_tools:
                    logger.warning(f"Agent tried to use unavailable tool: {tool_name}")
                    messages.append({
                        "role": "assistant",
                        "content": response
                    })
                    messages.append({
                        "role": "user",
                        "content": f"Tool '{tool_name}' is not available. Try another tool or return your result."
                    })
                    continue

                # Execute tool
                logger.info(f"Step {self.steps}: {self.agent.role} → {tool_name}")

                tool_result = await self.tool_manager.execute_tool(
                    agent_id=self.agent.id,
                    agent_role=self.agent.role,
                    tool_name=tool_name,
                    tool_params=tool_params,
                    org_id=self.org_id,
                    user_id=self.user_id,
                    conversation_id=self.conversation_id
                )

                # Check if approval required
                if tool_result.get("status") == "approval_required":
                    logger.info(f"Tool {tool_name} requires approval (id: {tool_result.get('approval_id')})")
                    # For demo: auto-approve research/read tools, halt on write tools
                    if tool_name in ["crm_read", "web_search", "calendar_read", "memory_search"]:
                        # Auto-approve read tools
                        tool_result = {
                            "status": "success",
                            "result": "Tool execution deferred (would need approval in production)"
                        }
                    else:
                        # Stop loop, wait for approval
                        return {
                            "status": "approval_pending",
                            "approval_id": tool_result.get("approval_id"),
                            "tool": tool_name,
                            "steps": self.steps,
                            "tokens_used": self.tokens_used
                        }

                # Track tool call
                self.tool_calls.append({
                    "step": self.steps,
                    "tool": tool_name,
                    "status": tool_result.get("status"),
                    "result": tool_result.get("result")
                })

                # Add to messages for context
                messages.append({
                    "role": "assistant",
                    "content": response
                })
                messages.append({
                    "role": "user",
                    "content": f"Tool result: {str(tool_result)[:500]}"  # Truncate long results
                })

        # Hit max steps
        logger.warning(f"Agent {self.agent.role} hit max steps ({self.max_steps})")
        return {
            "status": "max_steps_reached",
            "steps": self.steps,
            "tokens_used": self.tokens_used,
            "tool_calls": self.tool_calls
        }
