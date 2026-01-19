"""
OpenAI LLM provider implementation.

Supports GPT-4, GPT-3.5-turbo, and other OpenAI models.
"""

from typing import Optional

from openai import AsyncOpenAI

from app.core.logging import get_logger
from app.llm.base import LLMProvider
from app.llm.models import LLMResponse, LLMUsage

logger = get_logger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    # Pricing as of January 2024 (USD per 1K tokens)
    MODEL_PRICING = {
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-4-turbo-preview": {"prompt": 0.01, "completion": 0.03},
        "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
        "gpt-3.5-turbo-16k": {"prompt": 0.003, "completion": 0.004},
    }

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview", **kwargs):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (gpt-4, gpt-3.5-turbo, etc.)
            **kwargs: Additional OpenAI client parameters
        """
        super().__init__(model, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key, **kwargs)
        logger.info(f"openai_provider_initialized", extra={"model": model})

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def cost_per_1k_prompt_tokens(self) -> float:
        """Get prompt token cost for current model."""
        # Default to gpt-4 pricing if model not found
        pricing = self.MODEL_PRICING.get(self.model, self.MODEL_PRICING["gpt-4"])
        return pricing["prompt"]

    @property
    def cost_per_1k_completion_tokens(self) -> float:
        """Get completion token cost for current model."""
        pricing = self.MODEL_PRICING.get(self.model, self.MODEL_PRICING["gpt-4"])
        return pricing["completion"]

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion using OpenAI.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters

        Returns:
            LLMResponse with generated content
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return await self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion for chat messages.

        Args:
            messages: List of messages with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional OpenAI parameters

        Returns:
            LLMResponse with generated content
        """
        try:
            logger.info(
                "openai_request_started",
                extra={
                    "model": self.model,
                    "message_count": len(messages),
                    "temperature": temperature,
                }
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            # Extract usage information
            usage = None
            if response.usage:
                usage = LLMUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )
                usage.cost_usd = self.calculate_cost(
                    usage.prompt_tokens, usage.completion_tokens
                )

            content = response.choices[0].message.content

            logger.info(
                "openai_request_completed",
                extra={
                    "model": self.model,
                    "usage": usage.__dict__ if usage else None,
                    "cost_usd": usage.cost_usd if usage else 0,
                }
            )

            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.provider_name,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                raw_response=response.model_dump(),
            )

        except Exception as e:
            logger.error(
                "openai_request_failed",
                extra={"model": self.model, "error": str(e)}
            )
            raise

    async def embed(self, text: str) -> list[float]:
        """
        Generate embeddings using OpenAI.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(
                "openai_embedding_failed",
                extra={"error": str(e)}
            )
            raise
