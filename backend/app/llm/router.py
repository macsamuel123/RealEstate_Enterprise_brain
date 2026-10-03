"""LLM provider routing - Anthropic (primary), OpenAI (fallback), DeepSeek (budget)."""
from typing import Optional, List
from enum import Enum
import logging
from anthropic import Anthropic
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"  # Best quality, highest cost
    OPENAI = "openai"        # Good quality, medium cost
    DEEPSEEK = "deepseek"    # Good quality, lowest cost

# Initialize clients only if API keys are provided
anthropic_client = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
deepseek_client = OpenAI(
    api_key=settings.deepseek_api_key,
    base_url="https://api.deepseek.com"
) if settings.deepseek_api_key else None

class LLMRouter:
    """Routes LLM calls between providers with fallback and cost optimization."""

    def __init__(
        self,
        primary: LLMProvider = LLMProvider.ANTHROPIC,
        model: str = "claude-opus-5-5",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        use_budget_mode: bool = False
    ):
        self.primary = primary
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_budget_mode = use_budget_mode

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        messages: Optional[List[dict]] = None,
        cost_sensitive: bool = False
    ) -> str:
        """
        Get completion from LLM with fallback and cost optimization.

        cost_sensitive=True uses DeepSeek (cheapest, ~90% cheaper than Claude).
        Otherwise uses primary provider with fallback chain.
        """

        # Use DeepSeek for cost-sensitive tasks (research, analysis, summaries)
        if cost_sensitive or self.use_budget_mode:
            try:
                logger.info("Using DeepSeek for cost-sensitive task")
                return await self._complete_deepseek(system_prompt, user_message, messages)
            except Exception as e:
                logger.warning(f"DeepSeek failed, falling back to primary: {e}")

        # Try primary provider first
        try:
            if self.primary == LLMProvider.ANTHROPIC:
                return await self._complete_anthropic(system_prompt, user_message, messages)
            elif self.primary == LLMProvider.OPENAI:
                return await self._complete_openai(system_prompt, user_message, messages)
            else:
                return await self._complete_deepseek(system_prompt, user_message, messages)
        except Exception as e:
            logger.warning(f"Primary provider ({self.primary}) failed: {e}")

            # Fall back chain: Anthropic → OpenAI → DeepSeek
            fallback_chain = [
                LLMProvider.OPENAI if self.primary != LLMProvider.OPENAI else LLMProvider.ANTHROPIC,
                LLMProvider.DEEPSEEK
            ]

            for fallback in fallback_chain:
                logger.info(f"Falling back to {fallback}")
                try:
                    if fallback == LLMProvider.ANTHROPIC:
                        return await self._complete_anthropic(system_prompt, user_message, messages)
                    elif fallback == LLMProvider.OPENAI:
                        return await self._complete_openai(system_prompt, user_message, messages)
                    else:
                        return await self._complete_deepseek(system_prompt, user_message, messages)
                except Exception as fallback_e:
                    logger.warning(f"{fallback} failed: {fallback_e}")
                    continue

            logger.error("All LLM providers failed")
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

        messages.insert(0, {"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages
        )

        return response.choices[0].message.content

    async def _complete_deepseek(
        self,
        system_prompt: str,
        user_message: str,
        messages: Optional[List[dict]] = None
    ) -> str:
        """Complete using DeepSeek (OpenAI-compatible API)."""

        if messages is None:
            messages = []

        messages.insert(0, {"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages
        )

        return response.choices[0].message.content

def get_model_for_task(
    model: str = "claude-opus-5-5",
    temperature: float = 0.7,
    max_tokens: int = 2000,
    cost_sensitive: bool = False
) -> LLMRouter:
    """Get an LLM router configured for a specific task."""

    # Use DeepSeek for research/analysis, Claude for critical decisions
    primary = LLMProvider.DEEPSEEK if cost_sensitive else LLMProvider.ANTHROPIC

    return LLMRouter(
        primary=primary,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        use_budget_mode=cost_sensitive
    )

async def stream_completion(
    system_prompt: str,
    user_message: str,
    model: str = "claude-opus-5-5",
    temperature: float = 0.7,
    cost_sensitive: bool = False
):
    """Stream completion from LLM (useful for voice)."""

    client = deepseek_client if cost_sensitive else anthropic_client

    if cost_sensitive:
        # DeepSeek streaming
        with client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=1000,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            stream=True
        ) as stream:
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
    else:
        # Anthropic streaming
        with anthropic_client.messages.stream(
            model=model,
            max_tokens=1000,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        ) as stream:
            for text in stream.text_stream:
                yield text
