"""
Tests for LLM providers.

Tests the multi-model LLM support including OpenAI, Anthropic, and Ollama providers.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.llm import (
    DSPyLLMAdapter,
    LLMFactory,
    get_llm_provider,
    get_module_provider,
)
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.models import LLMResponse, LLMUsage
from app.llm.ollama_provider import OllamaProvider
from app.llm.openai_provider import OpenAIProvider


class TestLLMModels:
    """Test LLM data models."""

    def test_llm_usage_creation(self):
        """Test LLMUsage creation."""
        usage = LLMUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.cost_usd == 0.0  # Default implementation

    def test_llm_response_creation(self):
        """Test LLMResponse creation."""
        usage = LLMUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        response = LLMResponse(
            content="Test response",
            model="gpt-4",
            provider="openai",
            usage=usage,
            finish_reason="stop",
        )

        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.usage == usage
        assert response.finish_reason == "stop"
        assert response.cost_usd == 0.0


class TestOpenAIProvider:
    """Test OpenAI provider."""

    def test_initialization(self):
        """Test OpenAI provider initialization."""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")
        assert provider.model == "gpt-4"
        assert provider.provider_name == "openai"
        assert provider.cost_per_1k_prompt_tokens == 0.03
        assert provider.cost_per_1k_completion_tokens == 0.06

    def test_cost_calculation(self):
        """Test cost calculation."""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")
        cost = provider.calculate_cost(prompt_tokens=1000, completion_tokens=500)
        expected = (1000 / 1000 * 0.03) + (500 / 1000 * 0.06)
        assert cost == pytest.approx(expected)

    def test_gpt35_pricing(self):
        """Test GPT-3.5 pricing."""
        provider = OpenAIProvider(api_key="test-key", model="gpt-3.5-turbo")
        assert provider.cost_per_1k_prompt_tokens == 0.0005
        assert provider.cost_per_1k_completion_tokens == 0.0015

    @pytest.mark.asyncio
    async def test_complete_mock(self):
        """Test complete method with mocking."""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")

        # Mock the OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test response"), finish_reason="stop")]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        mock_response.model_dump = lambda: {}

        with patch.object(provider.client.chat.completions, "create", new=AsyncMock(return_value=mock_response)):
            response = await provider.complete("Test prompt")

            assert response.content == "Test response"
            assert response.provider == "openai"
            assert response.usage.prompt_tokens == 100
            assert response.usage.completion_tokens == 50


class TestAnthropicProvider:
    """Test Anthropic provider."""

    def test_initialization(self):
        """Test Anthropic provider initialization."""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-sonnet-20240229")
        assert provider.model == "claude-3-sonnet-20240229"
        assert provider.provider_name == "anthropic"
        assert provider.cost_per_1k_prompt_tokens == 0.003
        assert provider.cost_per_1k_completion_tokens == 0.015

    def test_opus_pricing(self):
        """Test Claude Opus pricing."""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-opus-20240229")
        assert provider.cost_per_1k_prompt_tokens == 0.015
        assert provider.cost_per_1k_completion_tokens == 0.075

    def test_haiku_pricing(self):
        """Test Claude Haiku pricing."""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-haiku-20240307")
        assert provider.cost_per_1k_prompt_tokens == 0.00025
        assert provider.cost_per_1k_completion_tokens == 0.00125

    @pytest.mark.asyncio
    async def test_complete_mock(self):
        """Test complete method with mocking."""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-sonnet-20240229")

        # Mock the Anthropic client
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)
        mock_response.stop_reason = "end_turn"
        mock_response.id = "test-id"
        mock_response.type = "message"
        mock_response.role = "assistant"

        with patch.object(provider.client.messages, "create", new=AsyncMock(return_value=mock_response)):
            response = await provider.complete("Test prompt")

            assert response.content == "Test response"
            assert response.provider == "anthropic"
            assert response.usage.prompt_tokens == 100
            assert response.usage.completion_tokens == 50

    def test_embeddings_not_supported(self):
        """Test that embeddings raise NotImplementedError."""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-sonnet-20240229")

        with pytest.raises(NotImplementedError):
            import asyncio
            asyncio.run(provider.embed("test text"))


class TestOllamaProvider:
    """Test Ollama provider."""

    def test_initialization(self):
        """Test Ollama provider initialization."""
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama2")
        assert provider.model == "llama2"
        assert provider.provider_name == "ollama"
        assert provider.cost_per_1k_prompt_tokens == 0.0  # Free
        assert provider.cost_per_1k_completion_tokens == 0.0

    def test_free_cost(self):
        """Test that Ollama is free."""
        provider = OllamaProvider(model="llama2")
        cost = provider.calculate_cost(prompt_tokens=1000, completion_tokens=500)
        assert cost == 0.0

    @pytest.mark.asyncio
    async def test_complete_mock(self):
        """Test complete method with mocking."""
        provider = OllamaProvider(base_url="http://localhost:11434", model="llama2")

        # Mock the HTTP client
        mock_response = Mock()
        mock_response.json = lambda: {
            "response": "Test response",
            "done_reason": "stop",
            "prompt_eval_count": 100,
            "eval_count": 50,
        }
        mock_response.raise_for_status = Mock()

        with patch.object(provider.client, "post", new=AsyncMock(return_value=mock_response)):
            response = await provider.complete("Test prompt")

            assert response.content == "Test response"
            assert response.provider == "ollama"
            assert response.usage.prompt_tokens == 100
            assert response.usage.completion_tokens == 50


class TestLLMFactory:
    """Test LLM Factory."""

    def test_create_openai_provider(self):
        """Test creating OpenAI provider."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = LLMFactory.create_provider("openai", "gpt-4", api_key="test-key")
            assert isinstance(provider, OpenAIProvider)
            assert provider.model == "gpt-4"

    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = LLMFactory.create_provider("anthropic", "claude-3-sonnet-20240229", api_key="test-key")
            assert isinstance(provider, AnthropicProvider)
            assert provider.model == "claude-3-sonnet-20240229"

    def test_create_ollama_provider(self):
        """Test creating Ollama provider."""
        provider = LLMFactory.create_provider("ollama", "llama2")
        assert isinstance(provider, OllamaProvider)
        assert provider.model == "llama2"

    def test_invalid_provider(self):
        """Test that invalid provider raises error."""
        from app.core.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError):
            LLMFactory.create_provider("invalid", "model")

    def test_cached_provider(self):
        """Test that cached provider returns same instance."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider1 = LLMFactory.get_cached_provider("openai", "gpt-4")
            provider2 = LLMFactory.get_cached_provider("openai", "gpt-4")
            assert provider1 is provider2

    def test_clear_cache(self):
        """Test clearing provider cache."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider1 = LLMFactory.get_cached_provider("openai", "gpt-4")
            LLMFactory.clear_cache()
            provider2 = LLMFactory.get_cached_provider("openai", "gpt-4")
            assert provider1 is not provider2


class TestDSPyAdapter:
    """Test DSPy adapter."""

    def test_initialization(self):
        """Test adapter initialization."""
        provider = OllamaProvider(model="llama2")
        adapter = DSPyLLMAdapter(provider=provider, max_tokens=500, temperature=0.7)

        assert adapter.provider == provider
        assert adapter.max_tokens == 500
        assert adapter.temperature == 0.7

    def test_repr(self):
        """Test adapter string representation."""
        provider = OllamaProvider(model="llama2")
        adapter = DSPyLLMAdapter(provider=provider)

        repr_str = repr(adapter)
        assert "DSPyLLMAdapter" in repr_str
        assert "ollama" in repr_str
        assert "llama2" in repr_str

    def test_copy(self):
        """Test adapter copy with updated parameters."""
        provider = OllamaProvider(model="llama2")
        adapter1 = DSPyLLMAdapter(provider=provider, max_tokens=500)
        adapter2 = adapter1.copy(max_tokens=1000)

        assert adapter2.max_tokens == 1000
        assert adapter1.max_tokens == 500
        assert adapter2.provider == adapter1.provider


class TestGetLLMProvider:
    """Test convenience functions."""

    @patch("app.llm.factory.settings")
    def test_get_llm_provider_default(self, mock_settings):
        """Test get_llm_provider with defaults."""
        mock_settings.LLM_PROVIDER = "ollama"
        mock_settings.LLM_MODEL = "llama2"
        mock_settings.OLLAMA_URL = "http://localhost:11434"

        provider = get_llm_provider()
        assert isinstance(provider, OllamaProvider)

    @patch("app.llm.factory.settings")
    def test_get_module_provider(self, mock_settings):
        """Test get_module_provider."""
        mock_settings.LLM_PROVIDER = "ollama"
        mock_settings.LLM_MODEL = "llama2"
        mock_settings.ANALYZER_LLM_PROVIDER = None
        mock_settings.ANALYZER_LLM_MODEL = None
        mock_settings.OLLAMA_URL = "http://localhost:11434"

        provider = get_module_provider("analyzer")
        assert isinstance(provider, OllamaProvider)
