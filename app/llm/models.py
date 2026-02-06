"""
Data models for LLM responses and usage tracking.
"""

from dataclasses import dataclass


@dataclass
class LLMUsage:
    """Token usage statistics."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    cost_usd: float = 0.0


@dataclass
class LLMResponse:
    """Unified response format from any LLM provider."""

    content: str
    model: str
    provider: str
    usage: LLMUsage | None = None
    finish_reason: str | None = None
    raw_response: dict | None = None

    @property
    def cost_usd(self) -> float:
        """Get cost of this response."""
        return self.usage.cost_usd if self.usage else 0.0
