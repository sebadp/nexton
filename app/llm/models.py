"""
Data models for LLM responses and usage tracking.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMUsage:
    """Token usage statistics."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    @property
    def cost_usd(self) -> float:
        """Calculate cost (to be overridden by provider)."""
        return 0.0


@dataclass
class LLMResponse:
    """Unified response format from any LLM provider."""

    content: str
    model: str
    provider: str
    usage: Optional[LLMUsage] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[dict] = None

    @property
    def cost_usd(self) -> float:
        """Get cost of this response."""
        return self.usage.cost_usd if self.usage else 0.0
