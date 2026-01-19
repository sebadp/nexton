"""
Ollama LLM provider implementation.

Supports local Ollama models (llama2, mistral, codellama, etc.).
"""

from typing import Optional

import httpx

from app.core.logging import get_logger
from app.llm.base import LLMProvider
from app.llm.models import LLMResponse, LLMUsage

logger = get_logger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama2",
        **kwargs
    ):
        """
        Initialize Ollama provider.

        Args:
            base_url: Ollama server URL
            model: Model name (llama2, mistral, codellama, etc.)
            **kwargs: Additional configuration
        """
        super().__init__(model, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)
        logger.info(f"ollama_provider_initialized", extra={"model": model, "base_url": base_url})

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def cost_per_1k_prompt_tokens(self) -> float:
        """Ollama is free (local)."""
        return 0.0

    @property
    def cost_per_1k_completion_tokens(self) -> float:
        """Ollama is free (local)."""
        return 0.0

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion using Ollama.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama parameters

        Returns:
            LLMResponse with generated content
        """
        try:
            logger.info(
                "ollama_request_started",
                extra={
                    "model": self.model,
                    "temperature": temperature,
                }
            )

            # Build request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }

            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt

            # Add max tokens if provided
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            # Add any additional options
            payload["options"].update(kwargs)

            # Make request to Ollama API
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()

            data = response.json()

            # Extract content
            content = data.get("response", "")

            # Extract usage information (if available)
            usage = None
            if "prompt_eval_count" in data or "eval_count" in data:
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                usage = LLMUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                )
                usage.cost_usd = 0.0  # Ollama is free

            logger.info(
                "ollama_request_completed",
                extra={
                    "model": self.model,
                    "usage": usage.__dict__ if usage else None,
                }
            )

            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.provider_name,
                usage=usage,
                finish_reason=data.get("done_reason"),
                raw_response=data,
            )

        except Exception as e:
            logger.error(
                "ollama_request_failed",
                extra={"model": self.model, "error": str(e)}
            )
            raise

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
            **kwargs: Additional Ollama parameters

        Returns:
            LLMResponse with generated content
        """
        try:
            logger.info(
                "ollama_chat_request_started",
                extra={
                    "model": self.model,
                    "message_count": len(messages),
                    "temperature": temperature,
                }
            )

            # Build request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            }

            # Add max tokens if provided
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            # Add any additional options
            payload["options"].update(kwargs)

            # Make request to Ollama chat API
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()

            data = response.json()

            # Extract content
            message = data.get("message", {})
            content = message.get("content", "")

            # Extract usage information
            usage = None
            if "prompt_eval_count" in data or "eval_count" in data:
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                usage = LLMUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                )
                usage.cost_usd = 0.0

            logger.info(
                "ollama_chat_request_completed",
                extra={
                    "model": self.model,
                    "usage": usage.__dict__ if usage else None,
                }
            )

            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.provider_name,
                usage=usage,
                finish_reason=data.get("done_reason"),
                raw_response=data,
            )

        except Exception as e:
            logger.error(
                "ollama_chat_request_failed",
                extra={"model": self.model, "error": str(e)}
            )
            raise

    async def embed(self, text: str) -> list[float]:
        """
        Generate embeddings using Ollama.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            response.raise_for_status()

            data = response.json()
            return data.get("embedding", [])

        except Exception as e:
            logger.error(
                "ollama_embedding_failed",
                extra={"model": self.model, "error": str(e)}
            )
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
