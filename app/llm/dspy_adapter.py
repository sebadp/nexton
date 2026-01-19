"""
DSPy adapter for our LLM providers.

Wraps our LLMProvider interface to work with DSPy's expected LM interface.
"""

import asyncio
import time
from typing import Any, Optional

import dspy

from app.core.logging import get_logger
from app.llm.base import LLMProvider
from app.observability import track_llm_error, track_llm_request

logger = get_logger(__name__)


class DSPyLLMAdapter(dspy.LM):
    """
    Adapter that wraps our LLMProvider to work with DSPy.

    DSPy expects certain methods on the LM class. This adapter provides
    that interface while using our unified LLMProvider underneath.
    """

    def __init__(
        self,
        provider: LLMProvider,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Initialize DSPy adapter.

        Args:
            provider: Our LLMProvider instance
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters
        """
        super().__init__(model=provider.model)
        self.provider = provider
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.kwargs = kwargs

        logger.info(
            "dspy_adapter_initialized",
            extra={
                "provider": provider.provider_name,
                "model": provider.model,
            }
        )

    def __call__(self, prompt: str, **kwargs) -> list[str]:
        """
        Synchronous call interface expected by DSPy.

        DSPy calls this method during pipeline execution.

        Args:
            prompt: The prompt string
            **kwargs: Additional parameters

        Returns:
            List of completion strings (DSPy expects list)
        """
        # Merge kwargs
        call_kwargs = {**self.kwargs, **kwargs}
        temperature = call_kwargs.pop("temperature", self.temperature)
        max_tokens = call_kwargs.pop("max_tokens", self.max_tokens)

        # Call async method synchronously
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we need to handle this differently
            # For now, we'll use run_until_complete which might not work in all cases
            # In production, DSPy should be called from sync context
            import nest_asyncio
            nest_asyncio.apply()

        start_time = time.time()
        status = "success"
        error_type = None

        try:
            response = loop.run_until_complete(
                self.provider.complete(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **call_kwargs
                )
            )

            duration = time.time() - start_time

            # Track metrics
            track_llm_request(
                provider=self.provider.provider_name,
                model=self.provider.model,
                status=status,
                duration_seconds=duration,
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                cost_usd=response.cost_usd,
            )

            # DSPy expects list of strings
            return [response.content]

        except Exception as e:
            status = "error"
            error_type = type(e).__name__
            duration = time.time() - start_time

            logger.error(
                "dspy_adapter_call_failed",
                extra={
                    "provider": self.provider.provider_name,
                    "model": self.provider.model,
                    "error": str(e),
                }
            )

            # Track error
            track_llm_error(self.provider.provider_name, error_type)
            track_llm_request(
                provider=self.provider.provider_name,
                model=self.provider.model,
                status=status,
                duration_seconds=duration,
            )

            raise

    async def acall(self, prompt: str, **kwargs) -> list[str]:
        """
        Async call interface.

        Args:
            prompt: The prompt string
            **kwargs: Additional parameters

        Returns:
            List of completion strings
        """
        # Merge kwargs
        call_kwargs = {**self.kwargs, **kwargs}
        temperature = call_kwargs.pop("temperature", self.temperature)
        max_tokens = call_kwargs.pop("max_tokens", self.max_tokens)

        start_time = time.time()
        status = "success"
        error_type = None

        try:
            response = await self.provider.complete(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                **call_kwargs
            )

            duration = time.time() - start_time

            # Track metrics
            track_llm_request(
                provider=self.provider.provider_name,
                model=self.provider.model,
                status=status,
                duration_seconds=duration,
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                cost_usd=response.cost_usd,
            )

            return [response.content]

        except Exception as e:
            status = "error"
            error_type = type(e).__name__
            duration = time.time() - start_time

            logger.error(
                "dspy_adapter_acall_failed",
                extra={
                    "provider": self.provider.provider_name,
                    "model": self.provider.model,
                    "error": str(e),
                }
            )

            # Track error
            track_llm_error(self.provider.provider_name, error_type)
            track_llm_request(
                provider=self.provider.provider_name,
                model=self.provider.model,
                status=status,
                duration_seconds=duration,
            )

            raise

    def copy(self, **kwargs) -> "DSPyLLMAdapter":
        """
        Create a copy of this adapter with updated parameters.

        Args:
            **kwargs: Parameters to update

        Returns:
            New DSPyLLMAdapter instance
        """
        new_kwargs = {**self.kwargs, **kwargs}
        return DSPyLLMAdapter(
            provider=self.provider,
            max_tokens=new_kwargs.pop("max_tokens", self.max_tokens),
            temperature=new_kwargs.pop("temperature", self.temperature),
            **new_kwargs
        )

    def __repr__(self) -> str:
        return f"DSPyLLMAdapter(provider={self.provider.provider_name}, model={self.provider.model})"
