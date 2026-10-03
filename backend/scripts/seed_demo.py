"""Seed demo data for Shawn Getty pilot."""
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/app')

from app.database import get_supabase
from app.models import (
    SubscriptionTier, UserRole, DealStage, ConversationChannel, MessageRole
)


async def seed_demo():
    """Create Getty Group demo org with seeded data."""

    supabase = get_supabase()

    # Create org
    org_id = uuid4()
    org = {
        "id": str(org_id),
        "name": "Getty Group",
        "slug": "getty-group",
        "subscription_tier": SubscriptionTier.SAAS.value
    }
    supabase.table("org").insert(org).execute()
    print(f"✅ Created org: Getty Group ({org_id})")

    # Create user (Shawn Getty)
    user_id = uuid4()
    user = {
        "id": str(user_id),
        "auth_user_id": str(uuid4()),
        "org_id": str(org_id),
        "email": "shawn@gettygroup.ca",
        "full_name": "Shawn Getty",
        "role": UserRole.OWNER.value
    }
    supabase.table("user").insert(user).execute()
    print(f"✅ Created user: Shawn Getty ({user_id})")

    # Create profile
    profile = {
        "org_id": str(org_id),
        "user_id": str(user_id),
        "business_name": "Getty Group",
        "business_type": "real_estate",
        "industry": "real_estate",
        "primary_market": "Calgary AB",
        "timezone": "America/Denver",
        "working_hours_start": "08:00",
        "working_hours_end": "18:00",
        "target_lead_response_time_minutes": 60,
        "communication_style": "Direct, results-focused",
        "morning_ritual": "Coffee + market briefing",
        "personal_interests": ["Stampeders football", "Golfing", "Real estate tech"],
        "completed_at": datetime.utcnow().isoformat()
    }
    supabase.table("profile").insert(profile).execute()
    print(f"✅ Created profile")

    # Seed 20 recruits
    recruits = [
        {"name": "Marcus Chen", "status": "silent_10d"},
        {"name": "Jennifer Williams", "status": "silent_10d"},
        {"name": "Chris Roberts", "status": "silent_10d"},
        {"name": "Sarah Johnson", "status": "active"},
        {"name": "Mike Thompson", "status": "active"},
        {"name": "Lisa Anderson", "status": "active"},
        {"name": "David Park", "status": "active"},
        {"name": "Rachel Green", "status": "active"},
        {"name": "Tom Brown", "status": "interested"},
        {"name": "Alex Martinez", "status": "interested"},
        {"name": "Emma Wilson", "status": "interested"},
        {"name": "James Liu", "status": "interested"},
        {"name": "Sophie Laurent", "status": "interested"},
        {"name": "Ryan O'Brien", "status": "interested"},
        {"name": "Katie Davis", "status": "interested"},
        {"name": "Nathan Gray", "status": "contacted"},
        {"name": "Olivia Smith", "status": "contacted"},
        {"name": "Lucas Miller", "status": "contacted"},
        {"name": "Ava Johnson", "status": "contacted"},
        {"name": "Ethan Taylor", "status": "contacted"},
    ]

    recruit_ids = []
    for recruit in recruits:
        contact = {
            "org_id": str(org_id),
            "name": recruit["name"],
            "email": f"{recruit['name'].lower().replace(' ', '.')}@example.com",
            "phone": f"403-555-{len(recruit_ids):04d}",
            "company": "Various",
            "relationship_type": "recruit"
        }
        result = supabase.table("contact").insert(contact).execute()
        recruit_id = result.data[0]["id"]
        recruit_ids.append(recruit_id)

    print(f"✅ Seeded {len(recruits)} recruits")

    # Seed 30 leads
    lead_data = [
        {"name": f"Lead_{i}", "status": "lead", "value": 450000 + i*10000}
        for i in range(30)
    ]

    for lead in lead_data:
        contact = {
            "org_id": str(org_id),
            "name": lead["name"],
            "email": f"{lead['name'].lower()}@example.com",
            "relationship_type": "lead"
        }
        contact_result = supabase.table("contact").insert(contact).execute()
        contact_id = contact_result.data[0]["id"]

        # Create deal
        deal = {
            "org_id": str(org_id),
            "user_id": str(user_id),
            "contact_id": contact_id,
            "title": f"{lead['name']} - {lead['status'].title()}",
            "stage": DealStage.LEAD.value,
            "value": lead["value"],
            "probability": 30
        }
        supabase.table("deal").insert(deal).execute()

    print(f"✅ Seeded 30 leads")

    # Seed 3 silent recruits with conversations
    silent_recruits = recruit_ids[:3]
    for idx, recruit_id in enumerate(silent_recruits):
        # Create conversation
        conv = {
            "org_id": str(org_id),
            "user_id": str(user_id),
            "channel": ConversationChannel.CHAT.value,
            "title": f"Recruit: {recruits[idx]['name']}"
        }
        conv_result = supabase.table("conversation").insert(conv).execute()
        conv_id = conv_result.data[0]["id"]

        # Add messages from 10+ days ago
        old_date = (datetime.utcnow() - timedelta(days=12)).isoformat()

        messages = [
            {"role": MessageRole.USER.value, "content": f"Hi {recruits[idx]['name']}, interested in joining Getty Group?"},
            {"role": MessageRole.ASSISTANT.value, "content": f"{recruits[idx]['name']}: Yes! Very interested. What's the structure?"},
            {"role": MessageRole.USER.value, "content": "We offer competitive desk costs and lead support. Let's talk more."},
            {"role": MessageRole.ASSISTANT.value, "content": f"{recruits[idx]['name']}: Sounds good. When are you free?"},
        ]

        for msg in messages:
            message = {
                "org_id": str(org_id),
                "conversation_id": conv_id,
                "role": msg["role"],
                "content": msg["content"],
                "created_at": old_date
            }
            supabase.table("message").insert(message).execute()

        # Add memory
        memory = {
            "org_id": str(org_id),
            "fact": f"{recruits[idx]['name']} interested in desk structure and lead support",
            "category": "relationship",
            "source": "conversation",
            "source_id": conv_id
        }
        supabase.table("memory").insert(memory).execute()

    print(f"✅ Seeded 3 silent recruits with conversation history")

    # Seed memories
    memories = [
        {"fact": "Shawn is passionate about lead quality and tech", "category": "preference"},
        {"fact": "Stampeders play Calgary tonight at 7 PM", "category": "personal"},
        {"fact": "Recent market: SE Calgary hot, inventory down", "category": "context"},
        {"fact": "Competitor: Davids Group hired 2 new agents", "category": "context"},
        {"fact": "Target response time: 60 minutes (currently 85 min)", "category": "operational"},
        {"fact": "Recruits Marcus, Jen, Chris silent 10+ days", "category": "operational"},
    ]

    for mem in memories:
        memory = {
            "org_id": str(org_id),
            "fact": mem["fact"],
            "category": mem["category"]
        }
        supabase.table("memory").insert(memory).execute()

    print(f"✅ Seeded {len(memories)} memories")

    # Create default agents
    from app.agents.orchestrator import create_default_agents
    await create_default_agents(org_id)

    print(f"\n✨ Demo seed complete!")
    print(f"Org ID: {org_id}")
    print(f"User ID: {user_id}")
    print(f"Ready for demo!")


if __name__ == "__main__":
    asyncio.run(seed_demo())
