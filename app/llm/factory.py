"""
LLM Factory for creating and managing LLM providers.

Provides centralized provider instantiation and configuration.
"""

from app.core.config import settings
from app.core.exceptions import ConfigurationError
from app.core.logging import get_logger
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.base import LLMProvider
from app.llm.ollama_provider import OllamaProvider
from app.llm.openai_provider import OpenAIProvider

logger = get_logger(__name__)


class LLMFactory:
    """Factory for creating LLM providers."""

    _providers: dict[str, type[LLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
    }

    _instances: dict[str, LLMProvider] = {}  # Cache instances

    @classmethod
    def create_provider(
        cls, provider_type: str | None = None, model: str | None = None, **kwargs
    ) -> LLMProvider:
        """
        Create LLM provider instance.

        Args:
            provider_type: Provider type (openai, anthropic, ollama)
                          If None, uses LLM_PROVIDER from settings
            model: Model name. If None, uses LLM_MODEL from settings
            **kwargs: Provider-specific configuration

        Returns:
            LLMProvider instance

        Raises:
            ConfigurationError: If provider type is invalid or missing credentials
        """
        # Use defaults from settings if not provided
        provider_type = provider_type or settings.LLM_PROVIDER
        model = model or settings.LLM_MODEL

        # Validate provider type
        if provider_type not in cls._providers:
            raise ConfigurationError(
                f"Invalid LLM provider: {provider_type}. "
                f"Supported: {', '.join(cls._providers.keys())}"
            )

        # Get provider class
        provider_class = cls._providers[provider_type]

        # Build provider-specific kwargs
        provider_kwargs = {"model": model}

        # OpenAI
        if provider_type == "openai":
            api_key = kwargs.get("api_key", settings.OPENAI_API_KEY)
            if not api_key:
                raise ConfigurationError("OPENAI_API_KEY is required for OpenAI provider")
            provider_kwargs["api_key"] = api_key

        # Anthropic
        elif provider_type == "anthropic":
            api_key = kwargs.get("api_key", settings.ANTHROPIC_API_KEY)
            if not api_key:
                raise ConfigurationError("ANTHROPIC_API_KEY is required for Anthropic provider")
            provider_kwargs["api_key"] = api_key

        # Ollama
        elif provider_type == "ollama":
            base_url = kwargs.get("base_url", settings.OLLAMA_URL)
            provider_kwargs["base_url"] = base_url

        # Add any additional kwargs
        provider_kwargs.update(kwargs)

        # Remove duplicates
        provider_kwargs.pop("api_key", None) if "api_key" in kwargs else None
        provider_kwargs.pop("base_url", None) if "base_url" in kwargs else None

        logger.info(
            "llm_provider_created",
            extra={
                "provider": provider_type,
                "model": model,
            },
        )

        return provider_class(**provider_kwargs)

    @classmethod
    def get_cached_provider(
        cls,
        provider_type: str | None = None,
        model: str | None = None,
    ) -> LLMProvider:
        """
        Get cached provider instance or create new one.

        Args:
            provider_type: Provider type
            model: Model name

        Returns:
            Cached or new LLMProvider instance
        """
        provider_type = provider_type or settings.LLM_PROVIDER
        model = model or settings.LLM_MODEL

        cache_key = f"{provider_type}:{model}"

        if cache_key not in cls._instances:
            cls._instances[cache_key] = cls.create_provider(provider_type, model)

        return cls._instances[cache_key]

    @classmethod
    def create_module_provider(cls, module_name: str) -> LLMProvider:
        """
        Create provider for specific DSPy module.

        Allows per-module LLM configuration:
        - ANALYZER_LLM_PROVIDER=openai
        - ANALYZER_LLM_MODEL=gpt-3.5-turbo
        - SCORER_LLM_PROVIDER=anthropic
        - SCORER_LLM_MODEL=claude-3-sonnet

        Args:
            module_name: Module name (analyzer, scorer, response_generator)

        Returns:
            LLMProvider instance configured for this module
        """
        module_upper = module_name.upper()

        # Check for module-specific configuration
        provider_env = f"{module_upper}_LLM_PROVIDER"
        model_env = f"{module_upper}_LLM_MODEL"

        provider_type = getattr(settings, provider_env, None) or settings.LLM_PROVIDER
        model = getattr(settings, model_env, None) or settings.LLM_MODEL

        logger.info(
            "module_provider_created",
            extra={
                "module": module_name,
                "provider": provider_type,
                "model": model,
            },
        )

        return cls.create_provider(provider_type, model)

    @classmethod
    def clear_cache(cls):
        """Clear cached provider instances."""
        cls._instances.clear()
        logger.info("llm_provider_cache_cleared")


def get_llm_provider(
    provider_type: str | None = None,
    model: str | None = None,
    cached: bool = True,
) -> LLMProvider:
    """
    Convenience function to get LLM provider.

    Args:
        provider_type: Provider type (openai, anthropic, ollama)
        model: Model name
        cached: If True, returns cached instance

    Returns:
        LLMProvider instance
    """
    if cached:
        return LLMFactory.get_cached_provider(provider_type, model)
    else:
        return LLMFactory.create_provider(provider_type, model)


def get_module_provider(module_name: str) -> LLMProvider:
    """
    Get LLM provider for specific module.

    Args:
        module_name: Module name (analyzer, scorer, response_generator)

    Returns:
        LLMProvider instance
    """
    return LLMFactory.create_module_provider(module_name)
