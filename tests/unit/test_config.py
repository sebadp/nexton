"""
Unit tests for configuration module.
"""
import os

import pytest

from app.core.config import Settings


class TestSettings:
    """Test Settings class."""

    def test_default_settings(self):
        """Test default settings are loaded correctly."""
        settings = Settings()

        assert settings.APP_NAME == "linkedin-agent"
        assert settings.ENV in ["development", "testing", "production"]
        assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]

    def test_environment_properties(self):
        """Test environment helper properties."""
        # Development
        settings = Settings(ENV="development")
        assert settings.is_development is True
        assert settings.is_production is False
        assert settings.is_testing is False

        # Production
        settings = Settings(ENV="production")
        assert settings.is_development is False
        assert settings.is_production is True
        assert settings.is_testing is False

        # Testing
        settings = Settings(ENV="test")
        assert settings.is_development is False
        assert settings.is_production is False
        assert settings.is_testing is True

    def test_database_url_validation(self):
        """Test DATABASE_URL validation."""
        # Valid URL
        settings = Settings(
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db"
        )
        assert "postgresql+asyncpg" in settings.DATABASE_URL

    def test_cors_origins_string_conversion(self):
        """Test CORS_ORIGINS conversion from string."""
        settings = Settings(CORS_ORIGINS="http://localhost:3000,http://localhost:8000")
        assert isinstance(settings.CORS_ORIGINS, list)
        assert len(settings.CORS_ORIGINS) == 2
        assert "http://localhost:3000" in settings.CORS_ORIGINS

    def test_cors_origins_list(self):
        """Test CORS_ORIGINS as list."""
        origins = ["http://localhost:3000", "http://localhost:8000"]
        settings = Settings(CORS_ORIGINS=origins)
        assert settings.CORS_ORIGINS == origins

    def test_ollama_settings(self):
        """Test Ollama configuration."""
        settings = Settings(
            OLLAMA_URL="http://localhost:11434",
            OLLAMA_MODEL="llama2",
            LLM_MAX_TOKENS=500,
            LLM_TEMPERATURE=0.7,
        )

        assert settings.OLLAMA_URL == "http://localhost:11434"
        assert settings.OLLAMA_MODEL == "llama2"
        assert settings.LLM_MAX_TOKENS == 500
        assert settings.LLM_TEMPERATURE == 0.7

    def test_profile_path(self):
        """Test profile path setting."""
        settings = Settings(PROFILE_PATH="config/profile.yaml")
        assert settings.PROFILE_PATH == "config/profile.yaml"
