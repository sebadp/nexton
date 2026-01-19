"""
Abstract base class for LLM providers.

Defines the interface that all LLM providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.llm.models import LLMResponse


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model: str, **kwargs):
        """
        Initialize LLM provider.

        Args:
            model: Model name/identifier
            **kwargs: Provider-specific configuration
        """
        self.model = model
        self.config = kwargs

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion for given prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with generated content and metadata
        """
        pass

    @abstractmethod
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
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with generated content and metadata
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name (e.g., 'openai', 'anthropic', 'ollama')."""
        pass

    @property
    @abstractmethod
    def cost_per_1k_prompt_tokens(self) -> float:
        """Cost per 1K prompt tokens in USD."""
        pass

    @property
    @abstractmethod
    def cost_per_1k_completion_tokens(self) -> float:
        """Cost per 1K completion tokens in USD."""
        pass

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate cost for given token usage.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Cost in USD
        """
        prompt_cost = (prompt_tokens / 1000) * self.cost_per_1k_prompt_tokens
        completion_cost = (completion_tokens / 1000) * self.cost_per_1k_completion_tokens
        return prompt_cost + completion_cost

    async def embed(self, text: str) -> list[float]:
        """
        Generate embeddings for text (optional).

        Args:
            text: Text to embed

        Returns:
            Embedding vector

        Raises:
            NotImplementedError: If provider doesn't support embeddings
        """
        raise NotImplementedError(f"{self.provider_name} does not support embeddings")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model='{self.model}')"
