"""Memory management - storing and retrieving durable facts with semantic search."""
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
from datetime import datetime

from app.database import get_supabase
from app.memory.embeddings import EmbeddingsService

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages organization's memory - facts, preferences, decisions."""

    def __init__(self, org_id: UUID):
        self.org_id = org_id
        self.supabase = get_supabase()
        self.embeddings = EmbeddingsService()

    async def write_memory(
        self,
        fact: str,
        category: str = "context",  # preference, decision, context, relationship, operational
        source: Optional[str] = None,
        source_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Write a durable fact to memory.

        Categories:
        - preference: user likes/dislikes (e.g. "Shawn prefers early morning calls")
        - decision: business decisions (e.g. "Decided to focus on recruiting, not sales")
        - context: background info (e.g. "Market is hot in Calgary")
        - relationship: about contacts/people (e.g. "John closes deals slowly but thoroughly")
        - operational: about business processes (e.g. "Average response time is 45 minutes")
        """

        try:
            # Generate embedding
            embedding = self.embeddings.embed_text(fact)

            # Write to database
            response = self.supabase.table("memory").insert({
                "org_id": str(self.org_id),
                "fact": fact,
                "category": category,
                "source": source,
                "source_id": str(source_id) if source_id else None,
                "embedding": embedding
            }).execute()

            logger.info(f"Wrote memory: {fact[:50]}...")
            return response.data[0] if response.data else {}

        except Exception as e:
            logger.error(f"Failed to write memory: {e}")
            raise

    async def recall_memories(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories most relevant to a query using semantic search.
        """

        try:
            # Generate embedding for query
            query_embedding = self.embeddings.embed_text(query)

            # TODO: Use pgvector for semantic search in Supabase
            # For now, fetch all memories and do client-side similarity search

            # Get all memories for this org
            response = self.supabase.table("memory").select("*").eq(
                "org_id", str(self.org_id)
            ).execute()

            memories = response.data or []

            if category:
                memories = [m for m in memories if m.get("category") == category]

            # Score by similarity
            scored = []
            for memory in memories:
                if memory.get("embedding"):
                    similarity = self.embeddings.cosine_similarity(
                        query_embedding,
                        memory["embedding"]
                    )
                    scored.append({**memory, "similarity": similarity})

            # Sort by similarity and return top-k
            scored.sort(key=lambda x: x["similarity"], reverse=True)
            return scored[:top_k]

        except Exception as e:
            logger.error(f"Failed to recall memories: {e}")
            return []

    async def extract_memories_from_conversation(
        self,
        conversation_text: str,
        context: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Extract durable facts from a conversation using LLM.

        Returns a list of facts to be written to memory.
        """

        # TODO: Use agent to extract durable facts from conversation
        # This is intentionally deferred to Layer 4+ when agents are built out
        # For now, return empty list - placeholder for future implementation

        logger.info("Memory extraction from conversation - placeholder for Layer 4+")
        return []

    async def update_contact_memory(
        self,
        contact_id: UUID,
        new_info: str
    ):
        """Update memory about a specific contact."""

        fact = f"About {contact_id}: {new_info}"
        return await self.write_memory(
            fact=fact,
            category="relationship",
            source="contact_update",
            source_id=contact_id
        )

    async def get_context_for_task(
        self,
        task_description: str,
        include_preferences: bool = True,
        include_decisions: bool = True,
        include_contacts: bool = True
    ) -> Dict[str, Any]:
        """
        Get all relevant context for a task (brief, agent action, etc).

        Returns organized context the agent can use.
        """

        context = {
            "task": task_description,
            "preferences": [],
            "decisions": [],
            "contacts": []
        }

        try:
            # Get relevant memories
            if include_preferences:
                prefs = await self.recall_memories(
                    task_description,
                    top_k=3,
                    category="preference"
                )
                context["preferences"] = [m["fact"] for m in prefs]

            if include_decisions:
                decs = await self.recall_memories(
                    task_description,
                    top_k=3,
                    category="decision"
                )
                context["decisions"] = [m["fact"] for m in decs]

            # Get relevant operational context
            ops = await self.recall_memories(
                task_description,
                top_k=2,
                category="operational"
            )
            context["operational"] = [m["fact"] for m in ops]

            return context

        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return context

    async def get_contact_context(self, contact_id: UUID) -> List[str]:
        """Get all memories about a specific contact."""

        try:
            response = self.supabase.table("memory").select("*").eq(
                "org_id", str(self.org_id)
            ).eq("source_id", str(contact_id)).execute()

            return [m["fact"] for m in (response.data or [])]

        except Exception as e:
            logger.error(f"Failed to get contact context: {e}")
            return []
