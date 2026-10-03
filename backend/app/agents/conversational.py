"""Conversational agent - Claude decides what tools to use, no keywords needed"""
from openai import OpenAI
from typing import Optional
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Use DeepSeek for testing (cheaper than Anthropic)
client = OpenAI(
    api_key=settings.deepseek_api_key,
    base_url="https://api.deepseek.com"
)

SYSTEM_PROMPT = """You are Shawn's Chief of Staff AI — a conversational agent that helps with daily operations.

You can access these tools:
- calendar_read: Get today's events and availability
- crm_read: Query contacts, deals, recruiting pipeline
- memory_recall: Retrieve facts about relationships and past decisions
- web_search: Research market trends, competitor activity
- email_draft: Compose emails (requires approval to send)
- email_send: Send approved emails
- calendar_write: Create calendar events

When the user asks a question:
1. Understand what they need
2. Call the appropriate tools to gather information
3. Synthesize into a clear, conversational response
4. Suggest actions if needed (but don't execute without approval)

Be brief and natural. Think like a smart assistant, not a robot.
When uncertain about names or details, ask clarifying questions.
For any action that sends/creates something, get explicit approval first."""


class ConversationalAgent:
    def __init__(self, org_id: str, user_id: str):
        self.org_id = org_id
        self.user_id = user_id
        self.conversation_history = []

    async def chat(self, user_message: str) -> str:
        """
        Have a conversation with DeepSeek.
        Returns: Spoken response text
        """
        logger.info(f"[DEBUG] ConversationalAgent.chat() called with: '{user_message}'")

        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        logger.info(f"[DEBUG] Calling DeepSeek with {len(self.conversation_history)} messages in history")

        try:
            # Call DeepSeek via OpenAI format (simple, no tools for now)
            response = client.chat.completions.create(
                model="deepseek-chat",
                max_tokens=500,
                messages=self.conversation_history,
            )
            logger.info(f"[DEBUG] DeepSeek API response received")

            # Get response text from DeepSeek
            assistant_message = response.choices[0].message.content
            logger.info(f"[DEBUG] DeepSeek response text: '{assistant_message}'")

            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            return assistant_message
        except Exception as e:
            logger.error(f"[ERROR] DeepSeek API call failed: {e}", exc_info=True)
            raise

    async def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return result"""
        try:
            if tool_name == "calendar_read":
                return await self._calendar_read(tool_input)
            elif tool_name == "crm_read":
                return await self._crm_read(tool_input)
            elif tool_name == "memory_recall":
                return await self._memory_recall(tool_input)
            elif tool_name == "web_search":
                return await self._web_search(tool_input)
            elif tool_name == "email_draft":
                return await self._email_draft(tool_input)
            elif tool_name == "email_send":
                return "[PENDING APPROVAL] Email ready to send. Read back needed before sending."
            elif tool_name == "calendar_write":
                return "[PENDING APPROVAL] Event ready to create. Read back needed before creating."
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    async def _calendar_read(self, input_data: dict) -> str:
        """Mock calendar read"""
        # TODO: Connect to real calendar API
        from app.seeds.getty_group_data import GETTY_GROUP_CALENDAR_TEMPLATES
        return json.dumps(GETTY_GROUP_CALENDAR_TEMPLATES, indent=2)

    async def _crm_read(self, input_data: dict) -> str:
        """Mock CRM read"""
        # TODO: Connect to real CRM
        from app.seeds.getty_group_data import GETTY_GROUP_CONTACTS, GETTY_GROUP_CRM_METRICS
        if input_data.get("query_type") == "active_deals":
            return json.dumps([c for c in GETTY_GROUP_CONTACTS if c.get("status") in ["hot", "active"]], indent=2)
        return json.dumps(GETTY_GROUP_CRM_METRICS, indent=2)

    async def _memory_recall(self, input_data: dict) -> str:
        """Mock memory recall"""
        # TODO: Connect to real memory system
        return f"Memory recall: {input_data.get('query')} (mock data)"

    async def _web_search(self, input_data: dict) -> str:
        """Mock web search"""
        # TODO: Connect to real search
        return f"Search results for: {input_data.get('query')} (mock data)"

    async def _email_draft(self, input_data: dict) -> str:
        """Draft email (no send)"""
        return f"""Email draft:
To: {input_data.get('to')}
Subject: {input_data.get('subject')}

{input_data.get('body')}

[Ready for review and approval before sending]"""
