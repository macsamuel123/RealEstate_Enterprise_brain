"""Task: Brief me - Morning briefing in <60 seconds"""
from datetime import datetime, timedelta
from anthropic import Anthropic
from app.services.calendar import get_today_events
from app.services.crm import get_unactioned_items
from app.memory.manager import MemoryManager
from app.tools.web_search import search

client = Anthropic()


async def brief_me(org_id: str, user_id: str) -> str:
    """
    Generate morning brief: calendar + inbox + live research
    Returns: Spoken summary (<=60 seconds)
    """

    # Gather data in parallel if possible
    calendar_events = await get_today_events(org_id, user_id)
    pending_items = await get_unactioned_items(org_id, user_id)
    memory = MemoryManager(org_id, user_id)

    # Get relevant memories (recent deals, key relationships)
    context = await memory.recall("brief_context", top_k=5)

    # Quick market research (if relevant)
    market_data = await search(f"real estate market calgary {datetime.now().strftime('%B %Y')}")

    # Synthesize into concise brief
    brief_text = await generate_brief(
        calendar_events=calendar_events,
        pending_items=pending_items,
        context=context,
        market_data=market_data,
    )

    return brief_text


async def generate_brief(calendar_events, pending_items, context, market_data) -> str:
    """Generate spoken brief using Claude"""

    calendar_summary = "\n".join(
        [f"- {e['title']} at {e['start_time']}" for e in calendar_events[:5]]
    ) or "No calendar events scheduled."

    pending_summary = "\n".join(
        [f"- {item['type']}: {item['subject']}" for item in pending_items[:3]]
    ) or "All caught up."

    market_summary = market_data[:200] if market_data else "Calgary market stable."

    prompt = f"""You are Shawn's morning briefing assistant. Synthesize this into a
SPOKEN brief that's under 60 seconds when read aloud. Be conversational, not robotic.

TODAY'S CALENDAR:
{calendar_summary}

PENDING ITEMS:
{pending_summary}

MARKET CONTEXT:
{market_summary}

RECENT CONTEXT (from memory):
{context}

Generate ONLY the spoken text. No list formatting, no bullet points.
Make it sound like you're talking to Shawn directly."""

    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()
