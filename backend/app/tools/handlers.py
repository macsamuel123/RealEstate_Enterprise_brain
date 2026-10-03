"""Tool handler implementations - actual tool execution logic."""
from typing import Dict, Any, List, Optional
from uuid import UUID
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ToolHandlerError(Exception):
    """Raised when a tool handler fails."""
    pass


class ToolHandlers:
    """Implementations of core tool handlers."""

    def __init__(self, supabase_client, gmail_service=None, calendar_service=None):
        self.supabase = supabase_client
        self.gmail = gmail_service
        self.calendar = calendar_service

    # =========================================================================
    # GMAIL TOOLS
    # =========================================================================

    async def gmail_read(
        self,
        org_id: UUID,
        user_id: UUID,
        query: str = "",
        limit: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Read emails from Gmail.

        Args:
            query: Gmail search query (e.g., "from:john@example.com")
            limit: Max emails to return

        Returns: {
            "emails": [
                {
                    "id": "message_id",
                    "from": "sender@example.com",
                    "subject": "Email subject",
                    "snippet": "First 100 chars...",
                    "timestamp": "2026-09-27T..."
                }
            ],
            "count": 5
        }
        """
        if not self.gmail:
            raise ToolHandlerError("Gmail service not connected")

        try:
            # TODO: Call Gmail API via self.gmail client
            # - Use user's OAuth token from Supabase Vault
            # - Execute search query
            # - Return formatted results

            # Stub: return mock data
            return {
                "emails": [
                    {
                        "id": "msg_123",
                        "from": "lead@example.com",
                        "subject": "Interested in listing",
                        "snippet": "I'm looking at your properties...",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ],
                "count": 1
            }
        except Exception as e:
            logger.error(f"Gmail read failed: {e}")
            raise ToolHandlerError(f"Failed to read Gmail: {e}")

    async def gmail_draft(
        self,
        org_id: UUID,
        user_id: UUID,
        to: str,
        subject: str,
        body: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Draft an email (not sent).

        Returns: {
            "status": "drafted",
            "draft_id": "draft_123",
            "to": "recipient@example.com",
            "subject": "Subject",
            "preview": "First 100 chars of body..."
        }
        """
        if not self.gmail:
            raise ToolHandlerError("Gmail service not connected")

        try:
            # TODO: Call Gmail API to create draft
            # - Don't send, just create as draft
            # - Return draft_id and preview

            # Stub: return mock draft
            return {
                "status": "drafted",
                "draft_id": f"draft_{hash(body) % 100000}",
                "to": to,
                "subject": subject,
                "preview": body[:100] + "..." if len(body) > 100 else body
            }
        except Exception as e:
            logger.error(f"Gmail draft failed: {e}")
            raise ToolHandlerError(f"Failed to draft email: {e}")

    # =========================================================================
    # CALENDAR TOOLS
    # =========================================================================

    async def calendar_read(
        self,
        org_id: UUID,
        user_id: UUID,
        days_ahead: int = 7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Read calendar events.

        Args:
            days_ahead: How many days ahead to fetch

        Returns: {
            "events": [
                {
                    "id": "event_id",
                    "title": "Event name",
                    "start": "2026-09-28T10:00:00",
                    "end": "2026-09-28T11:00:00",
                    "attendees": ["person@example.com"],
                    "description": "Event details"
                }
            ],
            "count": 3
        }
        """
        if not self.calendar:
            raise ToolHandlerError("Calendar service not connected")

        try:
            # TODO: Call Google Calendar API
            # - Get user's calendar via OAuth token
            # - Fetch events for next N days
            # - Return formatted list

            # Stub: return mock events
            now = datetime.utcnow()
            return {
                "events": [
                    {
                        "id": "evt_123",
                        "title": "Showing at 123 Main St",
                        "start": (now + timedelta(hours=2)).isoformat(),
                        "end": (now + timedelta(hours=3)).isoformat(),
                        "attendees": ["shawn@example.com"],
                        "description": "Property showing"
                    }
                ],
                "count": 1
            }
        except Exception as e:
            logger.error(f"Calendar read failed: {e}")
            raise ToolHandlerError(f"Failed to read calendar: {e}")

    # =========================================================================
    # WEB SEARCH
    # =========================================================================

    async def web_search(
        self,
        org_id: UUID,
        user_id: UUID,
        query: str,
        num_results: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search the web.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns: {
            "results": [
                {
                    "title": "Result title",
                    "url": "https://example.com",
                    "snippet": "Summary of result...",
                    "source": "example.com"
                }
            ],
            "count": 5
        }
        """
        try:
            from app.config import settings
            import httpx

            if not settings.serpapi_key:
                logger.warning("SerpAPI key not configured, returning mock results")
                return {
                    "results": [{
                        "title": "Calgary Real Estate Market 2026",
                        "url": "https://example.com",
                        "snippet": "Market trends...",
                        "source": "example.com"
                    }],
                    "count": 1
                }

            # Call SerpAPI
            params = {
                "q": query,
                "api_key": settings.serpapi_key,
                "num": num_results,
                "engine": "google"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

            # Extract organic results
            results = []
            organic_results = data.get("organic_results", [])

            for result in organic_results[:num_results]:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "source": result.get("source", "")
                })

            logger.info(f"Web search '{query}' → {len(results)} results")

            return {
                "results": results,
                "count": len(results)
            }

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            raise ToolHandlerError(f"Failed to search: {e}")

    # =========================================================================
    # CRM TOOLS
    # =========================================================================

    async def crm_read(
        self,
        org_id: UUID,
        user_id: UUID,
        entity_type: str,  # "contact", "deal", "lead"
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Read from CRM.

        Args:
            entity_type: Type of entity (contact, deal, lead)
            filters: Filter criteria (e.g., {"stage": "qualified"})
            limit: Max records

        Returns: {
            "entities": [...],
            "count": 5
        }
        """
        try:
            # Read from Supabase (Phase 1) or Zapier webhook (Phase 2)
            # For now, return mock data from database

            if entity_type == "contact":
                response = self.supabase.table("contact").select("*").eq(
                    "org_id", str(org_id)
                ).limit(limit).execute()
            elif entity_type == "deal":
                response = self.supabase.table("deal").select("*").eq(
                    "org_id", str(org_id)
                ).limit(limit).execute()
            else:
                raise ToolHandlerError(f"Unknown entity type: {entity_type}")

            entities = response.data or []
            return {
                "entities": entities,
                "count": len(entities)
            }
        except Exception as e:
            logger.error(f"CRM read failed: {e}")
            raise ToolHandlerError(f"Failed to read from CRM: {e}")

    async def crm_write(
        self,
        org_id: UUID,
        user_id: UUID,
        entity_type: str,  # "contact", "deal", "lead"
        action: str,  # "create", "update"
        data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Write to CRM (mock - actual write happens after approval).

        Args:
            entity_type: Type of entity
            action: "create" or "update"
            data: Fields to create/update

        Returns: {
            "status": "staged_for_approval",
            "action_id": "action_123",
            "changes": {...}
        }
        """
        try:
            # This tool creates an approval request, not actual CRM write
            # The actual write happens in approve_action()

            # Stage the change
            change_id = f"change_{hash(str(data)) % 100000}"

            logger.info(f"CRM {action} staged for approval: {change_id}")

            return {
                "status": "staged_for_approval",
                "change_id": change_id,
                "entity_type": entity_type,
                "action": action,
                "preview": data
            }
        except Exception as e:
            logger.error(f"CRM write staging failed: {e}")
            raise ToolHandlerError(f"Failed to stage CRM write: {e}")

    # =========================================================================
    # MEMORY TOOLS
    # =========================================================================

    async def memory_search(
        self,
        org_id: UUID,
        user_id: UUID,
        query: str,
        category: Optional[str] = None,
        limit: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search memory via semantic search.

        Args:
            query: Search query
            category: Filter by category (preference, decision, context, etc)
            limit: Max results

        Returns: {
            "memories": [
                {
                    "id": "mem_123",
                    "fact": "Shawn prefers luxury properties...",
                    "category": "preference",
                    "similarity": 0.87,
                    "source": "conversation_id"
                }
            ],
            "count": 3
        }
        """
        try:
            # TODO: Implement pgvector semantic search
            # - Get embedding for query
            # - Search memory table with cosine similarity
            # - Return top K results with similarity scores

            # Stub: return mock memory
            return {
                "memories": [
                    {
                        "id": "mem_123",
                        "fact": "Shawn prefers properties over $500k with 2+ acres",
                        "category": "preference",
                        "similarity": 0.92,
                        "source": "profile_onboarding"
                    }
                ],
                "count": 1
            }
        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            raise ToolHandlerError(f"Failed to search memory: {e}")

    # =========================================================================
    # STUBS FOR OTHER TOOLS (NotImplemented)
    # =========================================================================

    async def crm_update(self, **kwargs):
        raise NotImplementedError("crm_update not yet implemented")

    async def sms_send(self, **kwargs):
        raise NotImplementedError("sms_send requires Twilio integration")

    async def call_answer(self, **kwargs):
        raise NotImplementedError("call_answer requires Twilio voice integration")

    async def email_send(self, **kwargs):
        raise NotImplementedError("email_send requires approval first")

    async def document_create(self, **kwargs):
        raise NotImplementedError("document_create not yet implemented")

    async def analytics_read(self, **kwargs):
        raise NotImplementedError("analytics_read not yet implemented")

    async def agent_dispatch(self, **kwargs):
        raise NotImplementedError("agent_dispatch handled by orchestrator")

    async def agent_definition_write(self, **kwargs):
        raise NotImplementedError("agent_definition_write not yet implemented")

    # =========================================================================
    # DISPATCHER
    # =========================================================================

    async def execute(
        self,
        tool_name: str,
        org_id: UUID,
        user_id: UUID,
        **tool_params
    ) -> Dict[str, Any]:
        """Execute a tool by name."""

        if not hasattr(self, tool_name):
            raise ToolHandlerError(f"Unknown tool: {tool_name}")

        handler = getattr(self, tool_name)
        return await handler(
            org_id=org_id,
            user_id=user_id,
            **tool_params
        )
