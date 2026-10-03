"""Claude native agent with tool use loop."""
import json
import logging
import uuid
from typing import Optional
from anthropic import AsyncAnthropic
from app.config import settings, MODEL_TIERS, GMAIL_ALLOWLIST
from app.seeds.getty_group_data import GETTY_GROUP_CONTACTS

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """You are Shawn's Chief of Staff AI — a conversational assistant for Getty Group's real estate recruiting operations.

Your role: help Shawn manage his recruiting pipeline, schedule, and communication.

Context: Shawn is a real estate recruiting specialist focused on cold outreach and pipeline development. Keep responses to 1-2 spoken sentences max.

Available tools:
- calendar_read: Check today's events or search by date
- gmail_read: Read recent emails or search
- gmail_draft: Draft (not send) an email for review
- crm_read: Query contacts, deals, pipeline
- memory_search: Recall facts, decisions, context
- web_search: Research market trends or contact info
- request_approval: Ask permission to send/write/schedule (always use this for sends/writes)

Workflow:
1. Understand the user's request
2. Call appropriate tools to gather info
3. Synthesize into a brief, conversational response
4. If user asked for an action (send, schedule, create): request_approval first
5. Never execute sends/writes directly

Be natural and direct. Ask clarifying questions if needed."""

TOOLS = [
    {
        "name": "calendar_read",
        "description": "Get calendar events for a specific date or search for events",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date to query (YYYY-MM-DD, or 'today', 'tomorrow')"
                },
                "query": {
                    "type": "string",
                    "description": "Optional: search term for events"
                }
            },
            "required": ["date"]
        }
    },
    {
        "name": "gmail_read",
        "description": "Read recent emails or search for specific emails",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search term (sender, subject, etc) or 'recent' for last 5"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max emails to return (default 5)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "gmail_draft",
        "description": "Draft an email (does not send — requires approval to send)",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email or name"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body"}
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "crm_read",
        "description": "Query CRM: contacts, cold recruits, active deals, pipeline",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": ["cold_recruits", "active_deals", "hot_leads", "contact_details"],
                    "description": "What to query"
                },
                "contact_name": {
                    "type": "string",
                    "description": "Name to search (optional)"
                }
            },
            "required": ["query_type"]
        }
    },
    {
        "name": "memory_search",
        "description": "Recall facts, decisions, or context about contacts/deals",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to remember (e.g., 'Chen family preferences')"
                },
                "contact_name": {
                    "type": "string",
                    "description": "Person this relates to (optional)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the web for market trends, news, or contact research",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "request_approval",
        "description": "Request permission to execute an action (send email, schedule, etc)",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to execute (gmail_send, calendar_create, etc)"
                },
                "recipients": {
                    "type": "string",
                    "description": "Who this affects (email addresses or names)"
                },
                "payload": {
                    "type": "object",
                    "description": "Full action details (email body, event details, etc)"
                }
            },
            "required": ["action", "recipients", "payload"]
        }
    }
]


def _validate_gmail_recipient(recipient: str) -> tuple[bool, Optional[str]]:
    """Validate if recipient is in CRM and on allowlist."""
    # Find contact by email
    contact = None
    for c in GETTY_GROUP_CONTACTS:
        if c.get("email", "").lower() == recipient.lower():
            contact = c
            break

    if not contact:
        return False, f"Recipient '{recipient}' not found in CRM"

    if recipient not in GMAIL_ALLOWLIST:
        return False, f"Recipient '{recipient}' is not on the allowed send list (security policy)"

    return True, None


async def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool and return result."""
    logger.info(f"[TOOL] Executing {tool_name} with input: {tool_input}")

    try:
        if tool_name == "calendar_read":
            # Mock: return sample calendar data
            return json.dumps({
                "date": tool_input.get("date"),
                "events": [
                    {"time": "10:00 AM", "title": "Team standup", "duration": 30},
                    {"time": "2:00 PM", "title": "Cold call follow-ups", "duration": 90}
                ]
            })

        elif tool_name == "gmail_read":
            # Mock: return sample emails
            return json.dumps({
                "emails": [
                    {"from": "alex@example.com", "subject": "Re: Interview feedback", "preview": "Thanks for the call..."},
                    {"from": "priya@example.com", "subject": "Follow-up meeting", "preview": "Are you free next week..."}
                ]
            })

        elif tool_name == "gmail_draft":
            # Validate recipient against CRM and allowlist
            recipient = tool_input.get("to", "")
            is_valid, error_msg = _validate_gmail_recipient(recipient)

            if not is_valid:
                # Guard rule failed: reject and explain why
                return json.dumps({
                    "status": "rejected",
                    "error": error_msg,
                    "reason": "Cannot send to this recipient - " + error_msg
                })

            # Valid recipient: create approval request
            approval_id = str(uuid.uuid4())
            return json.dumps({
                "status": "pending_approval",
                "approval_id": approval_id,
                "to": recipient,
                "subject": tool_input.get("subject"),
                "body": tool_input.get("body"),
                "action": "gmail_send",
                "requires_approval": True
            })

        elif tool_name == "crm_read":
            # Mock: return CRM data
            query_type = tool_input.get("query_type")
            if query_type == "cold_recruits":
                return json.dumps({
                    "recruits": [
                        {"name": "Alex Thompson", "status": "first_contact", "company": "RBC"},
                        {"name": "Priya Patel", "status": "warm", "company": "TD"},
                        {"name": "David Ng", "status": "first_contact", "company": "BMO"}
                    ]
                })
            return json.dumps({"data": []})

        elif tool_name == "memory_search":
            # Mock: return memory
            return json.dumps({
                "query": tool_input.get("query"),
                "memories": ["Prefers email over calls", "Has experience in residential"]
            })

        elif tool_name == "web_search":
            # Mock: return search results
            return json.dumps({
                "query": tool_input.get("query"),
                "results": [
                    {"title": "Result 1", "url": "https://example.com/1", "snippet": "..."},
                ]
            })

        elif tool_name == "request_approval":
            # Validate action-specific requirements
            action = tool_input.get("action", "")
            recipients = tool_input.get("recipients", "")

            # For email sends, validate recipient against CRM and allowlist
            if action == "gmail_send":
                is_valid, error_msg = _validate_gmail_recipient(recipients)
                if not is_valid:
                    # Guard rule failed: tell Claude why and don't create approval
                    return json.dumps({
                        "status": "rejected",
                        "error": error_msg,
                        "action": action,
                        "recipients": recipients
                    })

            # Create an approval request with UUID
            approval_id = str(uuid.uuid4())
            return json.dumps({
                "status": "pending_approval",
                "action": action,
                "recipients": recipients,
                "approval_id": approval_id,
                "payload": tool_input.get("payload", "")
            })

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        logger.error(f"[TOOL ERROR] {tool_name}: {e}")
        return json.dumps({"error": str(e)})


async def chat(user_message: str, conversation_history: list, org_id: str, user_id: str) -> tuple[str, list, Optional[dict]]:
    """
    Run Claude with tools, up to 8 steps.
    Returns: (response_text, updated_history, pending_approval_if_any)
    """
    logger.info(f"[CLAUDE] Starting agent loop for: {user_message}")

    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    pending_approval = None
    max_steps = 8
    step = 0

    while step < max_steps:
        step += 1
        logger.info(f"[CLAUDE] Step {step}/{max_steps}")

        # Call Claude (standard tier for balanced performance/cost)
        response = await client.messages.create(
            model=MODEL_TIERS["standard"],
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=conversation_history
        )

        # Check stop reason
        if response.stop_reason == "end_turn":
            # Claude is done
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text = block.text
                    break

            logger.info(f"[CLAUDE] End turn. Response: {final_text}")
            conversation_history.append({
                "role": "assistant",
                "content": response.content
            })

            return final_text, conversation_history, pending_approval

        elif response.stop_reason == "tool_use":
            # Claude called tools
            logger.info(f"[CLAUDE] Tool use detected")

            # Append Claude's response (with tool calls)
            conversation_history.append({
                "role": "assistant",
                "content": response.content
            })

            # Execute tools
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    result = await execute_tool(tool_name, tool_input)

                    # Check if this is an approval request
                    try:
                        result_data = json.loads(result)
                        if result_data.get("status") == "pending_approval":
                            pending_approval = result_data
                    except:
                        pass

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Add tool results to history
            conversation_history.append({
                "role": "user",
                "content": tool_results
            })

        else:
            logger.warning(f"[CLAUDE] Unexpected stop reason: {response.stop_reason}")
            break

    logger.warning(f"[CLAUDE] Max steps ({max_steps}) reached")
    return "I hit my step limit. Please try again.", conversation_history, pending_approval
