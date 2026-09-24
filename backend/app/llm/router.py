"""LLM provider routing - Anthropic primary, OpenAI fallback."""
from typing import Optional, List
from enum import Enum
import logging
from anthropic import Anthropic
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"

# Initialize clients
anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
openai_client = OpenAI(api_key=settings.openai_api_key)

class LLMRouter:
    """Routes LLM calls between providers with fallback."""

    def __init__(
        self,
        primary: LLMProvider = LLMProvider.ANTHROPIC,
        model: str = "claude-opus-5-5",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        self.primary = primary
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        messages: Optional[List[dict]] = None
    ) -> str:
        """
        Get completion from LLM with fallback.
        """

        # Try primary provider first
        try:
            if self.primary == LLMProvider.ANTHROPIC:
                return await self._complete_anthropic(system_prompt, user_message, messages)
            else:
                return await self._complete_openai(system_prompt, user_message, messages)
        except Exception as e:
            logger.warning(f"Primary provider ({self.primary}) failed: {e}")

            # Fall back to other provider
            fallback = LLMProvider.OPENAI if self.primary == LLMProvider.ANTHROPIC else LLMProvider.ANTHROPIC
            logger.info(f"Falling back to {fallback}")

            try:
                if fallback == LLMProvider.ANTHROPIC:
                    return await self._complete_anthropic(system_prompt, user_message, messages)
                else:
                    return await self._complete_openai(system_prompt, user_message, messages)
            except Exception as fallback_e:
                logger.error(f"Both providers failed: {fallback_e}")
                raise

    async def _complete_anthropic(
        self,
        system_prompt: str,
        user_message: str,
        messages: Optional[List[dict]] = None
    ) -> str:
        """Complete using Anthropic Claude."""

        if messages is None:
            messages = []

        # Add user message
        messages.append({"role": "user", "content": user_message})

        response = anthropic_client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=messages
        )

        return response.content[0].text

    async def _complete_openai(
        self,
        system_prompt: str,
        user_message: str,
        messages: Optional[List[dict]] = None
    ) -> str:
        """Complete using OpenAI GPT."""

        if messages is None:
            messages = []

        # Add messages
        messages.insert(0, {"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",  # Adjust model as needed
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages
        )

        return response.choices[0].message.content

def get_model_for_task(
    model: str = "claude-opus-5-5",
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> LLMRouter:
    """Get an LLM router configured for a specific task."""

    # Default to Anthropic for most tasks
    primary = LLMProvider.ANTHROPIC

    # Use OpenAI for certain tasks if needed
    if "gpt" in model.lower():
        primary = LLMProvider.OPENAI

    return LLMRouter(
        primary=primary,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )

async def stream_completion(
    system_prompt: str,
    user_message: str,
    model: str = "claude-opus-5-5",
    temperature: float = 0.7
):
    """
    Stream completion from LLM.
    Useful for voice and real-time UI updates.
    """

    # Use Anthropic for streaming (better latency)
    with anthropic_client.messages.stream(
        model=model,
        max_tokens=1000,
        temperature=temperature,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    ) as stream:
        for text in stream.text_stream:
            yield text
