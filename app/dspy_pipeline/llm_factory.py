"""
LLM Factory for DSPy.

Creates LLM instances based on configuration (Ollama, OpenAI, Anthropic).
"""

import dspy

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> dspy.LM:
    """
    Get a DSPy LLM instance based on configuration.

    Args:
        provider: LLM provider (ollama, openai, anthropic). Uses settings.LLM_PROVIDER if None.
        model: Model name. Uses settings.LLM_MODEL if None.
        max_tokens: Max tokens. Uses settings.LLM_MAX_TOKENS if None.
        temperature: Temperature. Uses settings.LLM_TEMPERATURE if None.

    Returns:
        DSPy LM instance

    Raises:
        ValueError: If provider is not supported
    """
    provider = provider or settings.LLM_PROVIDER
    model = model or settings.LLM_MODEL
    max_tokens = max_tokens or settings.LLM_MAX_TOKENS
    temperature = temperature or settings.LLM_TEMPERATURE

    logger.info(
        "initializing_llm",
        provider=provider,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    if provider == "ollama":
        return _get_ollama_llm(model, max_tokens, temperature)
    elif provider == "openai":
        return _get_openai_llm(model, max_tokens, temperature)
    elif provider == "anthropic":
        return _get_anthropic_llm(model, max_tokens, temperature)
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. Supported providers: ollama, openai, anthropic"
        )


def _get_ollama_llm(model: str, max_tokens: int, temperature: float) -> dspy.LM:
    """
    Get Ollama LLM instance.

    Ollama runs locally and doesn't need API keys.
    Install with: curl -fsSL https://ollama.com/install.sh | sh
    Run with: ollama pull llama3.2 && ollama serve
    """
    # DSPy uses OpenAI-compatible API for Ollama
    lm = dspy.LM(
        model=f"ollama/{model}",
        api_base=settings.OLLAMA_URL,
        api_key="ollama",  # Ollama doesn't need a real key
        max_tokens=max_tokens,
        temperature=temperature,
    )

    logger.info(
        "ollama_llm_initialized",
        model=model,
        api_base=settings.OLLAMA_URL,
    )

    return lm


def _get_openai_llm(model: str, max_tokens: int, temperature: float) -> dspy.LM:
    """Get OpenAI LLM instance."""
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set. Please set it in .env or environment.")

    lm = dspy.LM(
        model=f"openai/{model}",
        api_key=settings.OPENAI_API_KEY,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    logger.info("openai_llm_initialized", model=model)
    return lm


def _get_anthropic_llm(model: str, max_tokens: int, temperature: float) -> dspy.LM:
    """Get Anthropic LLM instance."""
    if not settings.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set. Please set it in .env or environment.")

    lm = dspy.LM(
        model=f"anthropic/{model}",
        api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    logger.info("anthropic_llm_initialized", model=model)
    return lm
