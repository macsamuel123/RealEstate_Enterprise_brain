"""API routes for brief management."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from datetime import date

from app.auth.middleware import require_auth, TokenPayload
from app.briefs.scheduler import trigger_brief_now
from app.database import get_supabase

router = APIRouter()

@router.get("/briefs/today")
async def get_today_brief(token: TokenPayload = Depends(require_auth)):
    """Get today's brief for the user."""

    supabase = get_supabase()

    try:
        response = supabase.table("brief").select("*").eq(
            "user_id", str(token.user_id)
        ).eq("brief_date", str(date.today())).limit(1).execute()

        if response.data:
            return response.data[0]

        return {"message": "No brief generated yet"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/briefs/generate")
async def generate_brief_now(token: TokenPayload = Depends(require_auth)):
    """Manually trigger brief generation."""

    try:
        success = await trigger_brief_now(token.org_id, token.user_id, channel="email")

        if success:
            return {"status": "success", "message": "Brief generated and delivered"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate brief"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/briefs/history")
async def get_brief_history(limit: int = 7, token: TokenPayload = Depends(require_auth)):
    """Get past briefs (last N days)."""

    supabase = get_supabase()

    try:
        response = supabase.table("brief").select("*").eq(
            "user_id", str(token.user_id)
        ).order("brief_date", desc=True).limit(limit).execute()

        return response.data or []

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/briefs/schedule")
async def schedule_brief(
    delivery_time: str,  # HH:MM format
    delivery_channel: str = "email",
    token: TokenPayload = Depends(require_auth)
):
    """Schedule daily brief delivery."""

    # TODO: Validate time format
    # TODO: Store schedule in database
    # TODO: Register with APScheduler

    return {
        "status": "scheduled",
        "delivery_time": delivery_time,
        "delivery_channel": delivery_channel,
        "message": "Brief scheduling - placeholder for Layer 3 scheduling implementation"
    }
