"""Deliver briefs via email, SMS, voice."""
from typing import Dict, Any, Optional
from uuid import UUID
import logging
from datetime import datetime

from app.database import get_supabase
from app.config import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class BriefDeliverer:
    """Delivers briefs to users via their preferred channel."""

    def __init__(self, org_id: UUID, user_id: UUID):
        self.org_id = org_id
        self.user_id = user_id
        self.supabase = get_supabase()

    async def deliver_brief(
        self,
        brief_data: Dict[str, Any],
        channel: str = "email"  # email, sms, voice
    ) -> bool:
        """
        Deliver brief to user via specified channel.
        """

        try:
            if channel == "email":
                await self._deliver_email(brief_data)
            elif channel == "sms":
                await self._deliver_sms(brief_data)
            elif channel == "voice":
                await self._deliver_voice(brief_data)
            else:
                logger.warning(f"Unknown delivery channel: {channel}")
                return False

            # Log delivery
            await self._log_delivery(brief_data, channel)
            return True

        except Exception as e:
            logger.error(f"Failed to deliver brief via {channel}: {e}")
            return False

    async def _deliver_email(self, brief_data: Dict[str, Any]):
        """Deliver brief via email."""

        # Get user email
        user_response = self.supabase.table("users").select("email").eq(
            "id", str(self.user_id)
        ).limit(1).execute()

        if not user_response.data:
            raise ValueError(f"User {self.user_id} not found")

        user_email = user_response.data[0]["email"]

        # Compose email
        subject = f"Your Morning Brief — {brief_data.get('date', 'Today')}"

        # TODO: Render brief_data into beautiful HTML email
        # For now, simple text version

        body = self._format_brief_text(brief_data)

        # TODO: Use SendGrid or similar for reliable email delivery
        # For now, this is a placeholder

        logger.info(f"Would send email to {user_email}: {subject}")

        # Email would be sent here in production
        # smtplib.SMTP to send, or SendGrid API, etc

    async def _deliver_sms(self, brief_data: Dict[str, Any]):
        """Deliver brief via SMS (summary only)."""

        # TODO: Use Twilio to send SMS
        # Brief via SMS should be ultra-short - just the top 1-2 priority items

        logger.info(f"Would send SMS for brief on {brief_data.get('date')}")

    async def _deliver_voice(self, brief_data: Dict[str, Any]):
        """Deliver brief via voice call (future feature)."""

        # TODO: Use Twilio + ElevenLabs to call user and read brief
        # This is more complex - needs real-time speech synthesis
        # Defer to Layer 5

        logger.info(f"Voice delivery - placeholder for Layer 5")

    def _format_brief_text(self, brief_data: Dict[str, Any]) -> str:
        """Format brief data as readable text."""

        lines = []

        # Morning ritual (not in the text, done separately)
        lines.append("=" * 60)
        lines.append(f"Your Morning Brief — {brief_data.get('date')}")
        lines.append("=" * 60)

        # Day shape
        day_shape = brief_data.get("day_shape", {})
        lines.append("\n📅 Today's Shape")
        lines.append(day_shape.get("summary", "Your day ahead"))

        # Calendar
        calendar = brief_data.get("calendar", [])
        if calendar:
            lines.append("\n📆 Calendar")
            for event in calendar[:5]:  # Top 5 events
                lines.append(f"  • {event.get('time')} — {event.get('title')}")

        # Priority emails
        emails = brief_data.get("priority_emails", [])
        if emails:
            lines.append("\n📧 Priority Emails")
            for email in emails[:3]:  # Top 3
                lines.append(f"  • {email.get('from')} — {email.get('subject')[:50]}")

        # Market news
        market = brief_data.get("market_news", [])
        if market:
            lines.append("\n📊 Market & Industry")
            for item in market[:3]:
                lines.append(f"  • {item}")

        # Competitors
        competitors = brief_data.get("competitor_activity", [])
        if competitors:
            lines.append("\n🏢 Competitor Activity")
            for item in competitors[:2]:
                lines.append(f"  • {item}")

        # Personal interests
        personal = brief_data.get("personal_interests", [])
        if personal:
            lines.append("\n⭐ Your Interests")
            for item in personal[:2]:
                lines.append(f"  • {item}")

        lines.append("\n" + "=" * 60)
        lines.append("Have a great day!")

        return "\n".join(lines)

    async def _log_delivery(self, brief_data: Dict[str, Any], channel: str):
        """Log that brief was delivered."""

        try:
            self.supabase.table("brief").update({
                "delivered_at": datetime.utcnow().isoformat(),
                "delivery_channel": channel
            }).eq("user_id", str(self.user_id)).eq(
                "brief_date", brief_data.get("date")
            ).execute()

        except Exception as e:
            logger.warning(f"Failed to log delivery: {e}")
