"""Intent detection for voice commands"""
from enum import Enum
from anthropic import Anthropic

client = Anthropic()


class Intent(Enum):
    BRIEF_ME = "brief_me"
    WHO_AM_I_MEETING = "who_am_i_meeting"
    FOLLOW_UP_RECRUITS = "follow_up_recruits"
    BOOK_COFFEE = "book_coffee"
    WHAT_NEEDS_ATTENTION = "what_needs_attention"
    UNCLEAR = "unclear"


def detect_intent(question: str) -> tuple[Intent, dict]:
    """
    Detect intent from spoken question.
    Returns (intent, extracted_data)
    """

    # Quick regex patterns first (faster than LLM)
    q_lower = question.lower().strip()

    if any(
        x in q_lower
        for x in ["brief me", "morning brief", "what's my day", "give me a brief"]
    ):
        return Intent.BRIEF_ME, {}

    if any(
        x in q_lower for x in ["who am i meeting", "who's at", "meeting at", "appointment at"]
    ):
        # Extract time if present
        time_match = None
        if "at" in q_lower:
            parts = q_lower.split("at")[-1].strip()
            time_match = parts.split()[0] if parts else None
        return Intent.WHO_AM_I_MEETING, {"time": time_match}

    if any(x in q_lower for x in ["follow up", "cold recruits", "reach out"]):
        return Intent.FOLLOW_UP_RECRUITS, {}

    if any(x in q_lower for x in ["book", "schedule", "coffee", "meeting"]):
        # Extract name and day
        data = {}
        # Simple extraction: "Book coffee with NAME on DAY"
        if "with" in q_lower:
            after_with = q_lower.split("with")[-1]
            name = after_with.split()[0] if after_with.split() else None
            data["name"] = name

        if any(day in q_lower for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]):
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                if day in q_lower:
                    data["day"] = day
                    break

        return Intent.BOOK_COFFEE, data

    if any(x in q_lower for x in ["what needs", "needs attention", "priority", "urgent"]):
        return Intent.WHAT_NEEDS_ATTENTION, {}

    # Fallback to LLM for ambiguous cases
    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=100,
        system="""You are an intent classifier for a real estate agent's voice assistant.
Classify the user's intent into one of these categories:
- brief_me: Morning briefing / summary
- who_am_i_meeting: Calendar lookup
- follow_up_recruits: Follow-up emails
- book_coffee: Schedule meeting
- what_needs_attention: Priority tasks
- unclear: Can't determine

Respond with ONLY the category name, nothing else.""",
        messages=[{"role": "user", "content": question}],
    )

    intent_text = response.content[0].text.strip().lower()

    intent_map = {
        "brief_me": Intent.BRIEF_ME,
        "who_am_i_meeting": Intent.WHO_AM_I_MEETING,
        "follow_up_recruits": Intent.FOLLOW_UP_RECRUITS,
        "book_coffee": Intent.BOOK_COFFEE,
        "what_needs_attention": Intent.WHAT_NEEDS_ATTENTION,
        "unclear": Intent.UNCLEAR,
    }

    return intent_map.get(intent_text, Intent.UNCLEAR), {}
