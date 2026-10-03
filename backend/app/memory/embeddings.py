"""Embeddings service - converts text to vectors for semantic search."""
from typing import List
import logging
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=settings.openai_api_key)

class EmbeddingsService:
    """Generate embeddings for text (using OpenAI's text-embedding-3-small)."""

    model = "text-embedding-3-small"
    embedding_dimension = 1536

    @classmethod
    def embed_text(cls, text: str) -> List[float]:
        """
        Convert text to embedding vector.
        Returns a 1536-dimensional vector.
        """
        try:
            response = openai_client.embeddings.create(
                model=cls.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    @classmethod
    def embed_batch(cls, texts: List[str]) -> List[List[float]]:
        """Convert multiple texts to embeddings."""
        try:
            response = openai_client.embeddings.create(
                model=cls.model,
                input=texts
            )
            # Sort by index to ensure order matches input
            embeddings = sorted(response.data, key=lambda x: x.index)
            return [e.embedding for e in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise

    @classmethod
    def cosine_similarity(cls, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a * a for a in vec1) ** 0.5
        mag2 = sum(b * b for b in vec2) ** 0.5

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)
