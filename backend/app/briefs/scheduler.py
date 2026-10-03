"""Brief scheduler - generates and delivers briefs at configured times."""
import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, time, timedelta
import asyncio

# NOTE: APScheduler requires separate setup
# For production, use Celery + Redis or similar
# For local dev, this is a placeholder for the scheduling logic

logger = logging.getLogger(__name__)

class BriefScheduler:
    """
    Schedules brief generation and delivery.

    In production, this would be:
    - APScheduler for scheduling
    - Celery for background tasks
    - Redis for task queue

    For now, placeholder for the logic.
    """

    def __init__(self):
        self.jobs = {}  # org_id -> job_config

    def schedule_daily_brief(
        self,
        org_id: UUID,
        user_id: UUID,
        delivery_time: time,
        timezone: str = "America/Denver",
        delivery_channel: str = "email"
    ):
        """
        Schedule a daily brief for a user.

        Args:
            org_id: Organization ID
            user_id: User ID
            delivery_time: Time of day to deliver brief (e.g., 7:00 AM)
            timezone: User's timezone
            delivery_channel: "email", "sms", or "voice"
        """

        job_id = f"{org_id}_{user_id}"

        # TODO: Register with APScheduler
        # For now, log the intention

        logger.info(
            f"Scheduling brief for {user_id}: "
            f"{delivery_time.isoformat()} {timezone} via {delivery_channel}"
        )

        self.jobs[job_id] = {
            "org_id": org_id,
            "user_id": user_id,
            "delivery_time": delivery_time.isoformat(),
            "timezone": timezone,
            "delivery_channel": delivery_channel,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }

    def cancel_brief_schedule(self, org_id: UUID, user_id: UUID):
        """Cancel scheduled briefs for a user."""

        job_id = f"{org_id}_{user_id}"
        if job_id in self.jobs:
            self.jobs[job_id]["is_active"] = False
            logger.info(f"Cancelled brief schedule for {user_id}")

        # TODO: Remove from APScheduler

    def get_scheduled_briefs(self) -> dict:
        """Get all scheduled briefs."""
        return {k: v for k, v in self.jobs.items() if v.get("is_active")}


# Global scheduler instance
brief_scheduler = BriefScheduler()


async def run_daily_brief_cycle():
    """
    Background task that runs every minute to check if any briefs need to be generated.

    In production, this would be:
    - A Celery task running on a schedule
    - APScheduler handling timing
    - Redis storing job state

    For local dev, this is a placeholder for the logic.
    """

    # TODO: Implement the actual cycle
    # 1. Query all active brief schedules
    # 2. Check if it's time to generate/deliver
    # 3. Call BriefGenerator and BriefDeliverer
    # 4. Log results

    logger.info("Daily brief cycle - placeholder for scheduled task")


# For local testing: manual trigger
async def trigger_brief_now(org_id: UUID, user_id: UUID, channel: str = "email") -> bool:
    """Manually trigger a brief for testing."""

    from app.briefs.generator import BriefGenerator
    from app.briefs.deliverer import BriefDeliverer

    try:
        # Generate brief
        generator = BriefGenerator(org_id, user_id)
        brief_data = await generator.generate_brief()

        if "error" in brief_data:
            logger.error(f"Failed to generate brief: {brief_data['error']}")
            return False

        # Save to database
        await generator.save_brief(brief_data)

        # Deliver brief
        deliverer = BriefDeliverer(org_id, user_id)
        success = await deliverer.deliver_brief(brief_data, channel=channel)

        logger.info(f"Brief triggered for {user_id}: {success}")
        return success

    except Exception as e:
        logger.error(f"Failed to trigger brief: {e}", exc_info=True)
        return False
