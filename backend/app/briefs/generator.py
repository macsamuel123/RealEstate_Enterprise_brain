"""Generate morning briefs - the core Layer 3 feature."""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, date
import logging

from app.database import get_supabase
from app.memory.manager import MemoryManager
from app.llm.router import get_model_for_task
from app.models import Profile, Brief

logger = logging.getLogger(__name__)

class BriefGenerator:
    """Generates daily morning briefs for users."""

    def __init__(self, org_id: UUID, user_id: UUID):
        self.org_id = org_id
        self.user_id = user_id
        self.supabase = get_supabase()
        self.memory = MemoryManager(org_id)

    async def generate_brief(self, brief_date: date = None) -> Dict[str, Any]:
        """
        Generate a complete morning brief.

        Flow:
        1. Ground (music/prayer/meditation)
        2. Gentle transition (day shape)
        3. The Brief (calendar, emails, market, competitors, personal)
        """

        if brief_date is None:
            brief_date = date.today()

        logger.info(f"Generating brief for {self.user_id} on {brief_date}")

        try:
            # Load user profile
            profile = await self._get_profile()
            if not profile:
                logger.error(f"No profile found for user {self.user_id}")
                return {"error": "Profile not configured"}

            # Generate each section
            brief_data = {
                "date": brief_date.isoformat(),
                "morning_ritual": await self._generate_morning_ritual(profile),
                "day_shape": await self._generate_day_shape(profile),
                "calendar": await self._get_today_calendar(),
                "priority_emails": await self._get_priority_emails(),
                "market_news": await self._get_market_news(profile),
                "competitor_activity": await self._get_competitor_activity(profile),
                "personal_interests": await self._get_personal_interests(profile),
            }

            logger.info(f"Brief generated successfully for {self.user_id}")
            return brief_data

        except Exception as e:
            logger.error(f"Failed to generate brief: {e}", exc_info=True)
            return {"error": str(e)}

    async def _get_profile(self) -> Optional[Profile]:
        """Get user's profile."""
        try:
            response = self.supabase.table("profile").select("*").eq(
                "user_id", str(self.user_id)
            ).limit(1).execute()

            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get profile: {e}")
            return None

    async def _generate_morning_ritual(self, profile: Dict[str, Any]) -> str:
        """
        Generate the morning ritual section.
        No business content - just the user's chosen ritual.
        """

        ritual = profile.get("morning_ritual", "meditation")
        duration = profile.get("morning_ritual_duration_minutes", 15)

        # TODO: Integrate with external services (Spotify for music, etc)
        # For now, return a simple prompt

        if ritual == "music":
            return f"Music for {duration} minutes (suggest: calm instrumental or user's favorite playlist)"
        elif ritual == "prayer":
            return f"Prayer or reflection for {duration} minutes"
        elif ritual == "meditation":
            return f"Meditation for {duration} minutes (suggest: Headspace or Calm app)"
        elif ritual == "motivational":
            return f"Motivational content for {duration} minutes (suggest: daily podcast or speech)"
        else:
            return f"{ritual.capitalize()} for {duration} minutes"

    async def _generate_day_shape(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gentle transition - time until first commitment, whether anything urgent landed.
        """

        # TODO: Get user's calendar and compute time to first meeting
        # For now, return placeholder

        return {
            "status": "No urgent items overnight",
            "time_until_first_commitment": "2 hours",
            "has_urgent_emails": False,
            "summary": "Morning is clear - you've got time"
        }

    async def _get_today_calendar(self) -> List[Dict[str, Any]]:
        """Get today's calendar events."""

        # TODO: Connect to Google Calendar via stored connection
        # For now, return empty (placeholder)

        return []

    async def _get_priority_emails(self) -> List[Dict[str, Any]]:
        """Get priority emails from inbox."""

        # TODO: Connect to Gmail via stored connection
        # Filter for: 1) from known important contacts, 2) has keywords (urgent, deal, closing, etc)
        # For now, return empty (placeholder)

        return []

    async def _get_market_news(self, profile: Dict[str, Any]) -> List[str]:
        """
        Get market/industry news relevant to user's business.
        For real estate: rates, migration, policy, buyer behavior.
        """

        # TODO: Implement news aggregation
        # Use LLM to synthesize news into actionable insights
        # For now, return placeholder

        insights = []

        # Example for real estate in Calgary
        if "Calgary" in profile.get("primary_market", ""):
            insights.append("Rates held steady - expect buyers to move this week")
            insights.append("Migration to Alberta up 8% YoY - buyers looking at Calgary specifically")

        return insights

    async def _get_competitor_activity(self, profile: Dict[str, Any]) -> List[str]:
        """
        Get what competitors are doing.
        For real estate: listing volume, sold units, new listings.
        """

        # TODO: Implement competitor tracking
        # Track known competitors' listing activity, sold units, etc
        # For now, return placeholder

        activity = []

        competitors = profile.get("competitors", [])
        if competitors:
            activity.append(f"Monitoring {len(competitors)} known competitors")
            activity.append("Competitor X uploaded 3 new listings this week")

        return activity

    async def _get_personal_interests(self, profile: Dict[str, Any]) -> List[str]:
        """Get updates on personal interests (sports, politics, etc)."""

        # TODO: Implement news aggregation for personal interests
        # For now, return placeholder

        interests = []

        personal = profile.get("personal_interests", [])
        if personal:
            interests.append(f"Watching {len(personal)} topics")
            # Example
            if "Canadian politics" in personal:
                interests.append("Bank of Canada held rates - expect this to affect housing costs")

        return interests

    async def save_brief(self, brief_data: Dict[str, Any]) -> Brief:
        """Save generated brief to database."""

        try:
            response = self.supabase.table("brief").insert({
                "org_id": str(self.org_id),
                "user_id": str(self.user_id),
                "brief_date": brief_data.get("date"),
                "content": brief_data
            }).execute()

            logger.info(f"Saved brief for {self.user_id}")
            return response.data[0] if response.data else {}

        except Exception as e:
            logger.error(f"Failed to save brief: {e}")
            raise
