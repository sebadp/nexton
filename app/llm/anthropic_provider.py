"""
Anthropic Claude LLM provider implementation.

Supports Claude 3 models (Opus, Sonnet, Haiku).
"""

from typing import Optional

from anthropic import AsyncAnthropic

from app.core.logging import get_logger
from app.llm.base import LLMProvider
from app.llm.models import LLMResponse, LLMUsage

logger = get_logger(__name__)


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    # Pricing as of January 2024 (USD per 1K tokens)
    MODEL_PRICING = {
        "claude-3-opus-20240229": {"prompt": 0.015, "completion": 0.075},
        "claude-3-sonnet-20240229": {"prompt": 0.003, "completion": 0.015},
        "claude-3-haiku-20240307": {"prompt": 0.00025, "completion": 0.00125},
        # Aliases
        "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
        "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
        "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
    }

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", **kwargs):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model name (claude-3-opus, claude-3-sonnet, claude-3-haiku)
            **kwargs: Additional Anthropic client parameters
        """
        super().__init__(model, **kwargs)
        self.client = AsyncAnthropic(api_key=api_key, **kwargs)
        logger.info(f"anthropic_provider_initialized", extra={"model": model})

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def cost_per_1k_prompt_tokens(self) -> float:
        """Get prompt token cost for current model."""
        # Default to sonnet pricing if model not found
        pricing = self.MODEL_PRICING.get(
            self.model,
            self.MODEL_PRICING["claude-3-sonnet"]
        )
        return pricing["prompt"]

    @property
    def cost_per_1k_completion_tokens(self) -> float:
        """Get completion token cost for current model."""
        pricing = self.MODEL_PRICING.get(
            self.model,
            self.MODEL_PRICING["claude-3-sonnet"]
        )
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
        Generate completion using Anthropic Claude.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Anthropic parameters

        Returns:
            LLMResponse with generated content
        """
        messages = [{"role": "user", "content": prompt}]

        return await self.chat(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens or 4096,  # Anthropic requires max_tokens
            **kwargs
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion for chat messages.

        Args:
            messages: List of messages with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate (required by Anthropic)
            system_prompt: Optional system prompt
            **kwargs: Additional Anthropic parameters

        Returns:
            LLMResponse with generated content
        """
        try:
            logger.info(
                "anthropic_request_started",
                extra={
                    "model": self.model,
                    "message_count": len(messages),
                    "temperature": temperature,
                }
            )

            # Anthropic requires max_tokens
            if max_tokens is None:
                max_tokens = 4096

            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }

            # Add system prompt if provided
            if system_prompt:
                request_params["system"] = system_prompt

            response = await self.client.messages.create(**request_params)

            # Extract usage information
            usage = None
            if response.usage:
                usage = LLMUsage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                )
                usage.cost_usd = self.calculate_cost(
                    usage.prompt_tokens, usage.completion_tokens
                )

            # Extract content (Claude returns list of content blocks)
            content = ""
            if response.content:
                content = response.content[0].text if response.content else ""

            logger.info(
                "anthropic_request_completed",
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
                finish_reason=response.stop_reason,
                raw_response={
                    "id": response.id,
                    "type": response.type,
                    "role": response.role,
                    "stop_reason": response.stop_reason,
                },
            )

        except Exception as e:
            logger.error(
                "anthropic_request_failed",
                extra={"model": self.model, "error": str(e)}
            )
            raise

    async def embed(self, text: str) -> list[float]:
        """
        Anthropic does not support embeddings.

        Raises:
            NotImplementedError: Always raises as Anthropic doesn't support embeddings
        """
        raise NotImplementedError("Anthropic does not support embeddings")
