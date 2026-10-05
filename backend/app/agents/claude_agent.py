"""DeepSeek agent with tool use loop (using OpenAI-compatible API)."""
import json
import logging
import uuid
from typing import Optional
from openai import AsyncOpenAI
from app.config import settings, GMAIL_ALLOWLIST
from app.seeds.getty_group_data import GETTY_GROUP_CONTACTS

logger = logging.getLogger(__name__)

# Use DeepSeek via OpenAI-compatible API
if not settings.deepseek_api_key:
    raise ValueError("DEEPSEEK_API_KEY not set in .env")

client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url="https://api.deepseek.com"
)

MODEL = "deepseek-chat"

SYSTEM_PROMPT = """You are Shawn's Chief of Staff AI — a conversational assistant for Getty Group's real estate recruiting operations.

Your role: help Shawn manage his recruiting pipeline, schedule, and communication.

Context: Shawn is a real estate recruiting specialist focused on cold outreach and pipeline development. Keep responses to 1-2 spoken sentences max.

Available tools:
1. calendar_read: Get calendar events for a specific date
2. crm_read: Query contacts, deals, recruiting pipeline
3. memory_search: Retrieve facts about relationships and past decisions
4. web_search: Research market trends, competitor activity
5. gmail_draft: Compose emails (requires approval to send)
6. request_approval: Request permission to execute an action

Workflow:
1. Understand what the user is asking
2. Use relevant tools to gather information
3. Synthesize into a clear, conversational response
4. If user asked for an action (send, schedule, create): request_approval first
5. Never execute sends/writes directly

Be natural and direct. Ask clarifying questions if needed."""

# Tool definitions (OpenAI format)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calendar_read",
            "description": "Get calendar events for a specific date or search for events",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date to get events for (YYYY-MM-DD)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for events (optional)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crm_read",
            "description": "Query contacts, deals, recruiting pipeline",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "description": "Type of query: contacts, deals, pipeline, metrics"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory_search",
            "description": "Search for remembered facts about relationships and past decisions",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to remember or search for"
                    },
                    "contact_name": {
                        "type": "string",
                        "description": "Person this relates to (optional)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Research market trends, competitor activity, or other web information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "gmail_draft",
            "description": "Draft an email (compose without sending)",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Email recipient"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body/message"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_approval",
            "description": "Request permission to execute an action (send email, schedule, etc)",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action type: gmail_send, calendar_create, etc"
                    },
                    "recipients": {
                        "type": "string",
                        "description": "Who this affects (email addresses or names)"
                    },
                    "payload": {
                        "type": "string",
                        "description": "Action details (email body, event details, etc)"
                    }
                },
                "required": ["action", "recipients", "payload"]
            }
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
            # Mock: return calendar data
            return json.dumps({
                "date": tool_input.get("date"),
                "events": [
                    {"time": "9:00 AM", "title": "Team standup"},
                    {"time": "10:00 AM", "title": "Admin time"},
                    {"time": "2:00 PM", "title": "Cold calls"}
                ]
            })

        elif tool_name == "crm_read":
            # Mock: return CRM data
            query_type = tool_input.get("query_type", "metrics")
            if query_type == "pipeline":
                return json.dumps({
                    "active_deals": 3,
                    "pipeline_value": "$2.7M",
                    "hot_leads": 2,
                    "cold_recruits": 3
                })
            else:
                return json.dumps({
                    "contacts_count": 9,
                    "active_deals": 3,
                    "pipeline_value": "$2.7M"
                })

        elif tool_name == "memory_search":
            # Mock: return memory
            return json.dumps({
                "query": tool_input.get("query"),
                "results": "No memories yet (memory system coming soon)"
            })

        elif tool_name == "web_search":
            # Mock: return search results
            return json.dumps({
                "query": tool_input.get("query"),
                "results": [
                    {"title": "Result 1", "url": "https://example.com/1", "snippet": "..."},
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

            # Valid recipient: draft ready (will need approval)
            return json.dumps({
                "status": "draft_ready",
                "to": recipient,
                "subject": tool_input.get("subject"),
                "body": tool_input.get("body"),
                "requires_approval": True
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
    Run DeepSeek with tools, up to 8 steps.
    Returns: (response_text, updated_history, pending_approval_if_any)
    """
    logger.info(f"[DEEPSEEK] ===== STARTING CHAT =====")
    logger.info(f"[DEEPSEEK] User message: '{user_message}'")
    logger.info(f"[DEEPSEEK] Message length: {len(user_message)} chars")
    logger.info(f"[DEEPSEEK] History length: {len(conversation_history)} messages")

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
        logger.info(f"\n[DEEPSEEK] === STEP {step}/{max_steps} ===")
        logger.info(f"[DEEPSEEK] Calling DeepSeek API with {len(conversation_history)} messages in history...")

        try:
            # Call DeepSeek with tools
            response = await client.chat.completions.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=conversation_history
            )

            logger.info(f"[DEEPSEEK] API response received!")
            logger.info(f"[DEEPSEEK] Stop reason: {response.stop_reason}")
            logger.info(f"[DEEPSEEK] Choices count: {len(response.choices)}")
        except Exception as e:
            logger.error(f"[DEEPSEEK] API ERROR: {e}", exc_info=True)
            raise

        # Check stop reason
        if response.stop_reason == "stop":
            # DeepSeek is done
            final_text = response.choices[0].message.content or ""

            logger.info(f"[DEEPSEEK] End turn. Response: {final_text}")
            conversation_history.append({
                "role": "assistant",
                "content": final_text
            })

            return final_text, conversation_history, pending_approval

        elif response.stop_reason == "tool_calls":
            # DeepSeek called tools
            logger.info(f"[DEEPSEEK] Tool use detected")

            # Append Claude's response (with tool calls)
            conversation_history.append({
                "role": "assistant",
                "content": response.choices[0].message.content,
                "tool_calls": response.choices[0].message.tool_calls
            })

            # Execute tools
            tool_results = []
            for tool_call in response.choices[0].message.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)

                result = await execute_tool(tool_name, tool_input)

                # Check if this is an approval request
                try:
                    result_data = json.loads(result)
                    if result_data.get("status") == "pending_approval":
                        pending_approval = result_data
                except:
                    pass

                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_name,
                    "content": result
                })

            # Add tool results to history
            conversation_history.append({
                "role": "user",
                "content": tool_results
            })

        else:
            logger.warning(f"[DEEPSEEK] Unexpected stop reason: {response.stop_reason}")
            break

    logger.warning(f"[DEEPSEEK] Max steps ({max_steps}) reached")
    return "I hit my step limit. Please try again.", conversation_history, pending_approval
