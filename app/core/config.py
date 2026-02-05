"""
Application configuration using Pydantic Settings.
Reads from environment variables and .env file.
"""

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "linkedin-agent"
    APP_VERSION: str = "1.0.0"
    ENV: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # API
    API_V1_PREFIX: str = "/api/v1"
    API_RATE_LIMIT: int = 100

    # Security
    SECRET_KEY: str = "change-this-to-a-random-secret-key-in-production"
    ALLOWED_HOSTS: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Database (Optional for lite mode)
    DATABASE_URL: str | None = None
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0

    # Redis (Optional for lite mode)
    REDIS_URL: str | None = None
    REDIS_MAX_CONNECTIONS: int = 50

    # AI/ML - Multi-LLM Support
    LLM_PROVIDER: str = "ollama"  # openai, anthropic, ollama
    LLM_MODEL: str = "llama2"
    LLM_MAX_TOKENS: int = 500
    LLM_TEMPERATURE: float = 0.7
    LLM_TIMEOUT: int = 30

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    EMBEDDING_MODEL_NAME: str = "llama2"

    # Per-module LLM configuration (optional)
    ANALYZER_LLM_PROVIDER: str | None = None
    ANALYZER_LLM_MODEL: str | None = None
    SCORER_LLM_PROVIDER: str | None = None
    SCORER_LLM_MODEL: str | None = None
    RESPONSE_LLM_PROVIDER: str | None = None
    RESPONSE_LLM_MODEL: str | None = None

    # Celery (Optional for lite mode)
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    CELERY_WORKER_CONCURRENCY: int = 4

    # Observability
    OTEL_ENABLED: bool = True
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4318"
    OTEL_SERVICE_NAME: str = "linkedin-agent"
    OTEL_EXCLUDED_URLS: str = "/health,/metrics,/docs,/redoc,/openapi.json"
    PROMETHEUS_MULTIPROC_DIR: str = "/tmp/prometheus"

    # LinkedIn
    LINKEDIN_EMAIL: str = ""
    LINKEDIN_PASSWORD: str = ""
    SCRAPER_HEADLESS: bool = True
    SCRAPER_SLOWMO: int = 100
    SCRAPER_TIMEOUT: int = 30000
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_RATE_LIMIT: int = 10
    SCRAPER_COOLDOWN: int = 300

    # User Profile
    PROFILE_PATH: str = "config/profile.yaml"

    # Email (SMTP Configuration)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USE_TLS: bool = False
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@linkedin-agent.local"

    # Notifications
    NOTIFICATION_EMAIL: str = ""  # Email to receive opportunity notifications
    NOTIFICATION_ENABLED: bool = True
    NOTIFICATION_TIER_THRESHOLD: list[str] = Field(default_factory=lambda: ["A", "B"])
    NOTIFICATION_SCORE_THRESHOLD: int = 0  # Minimum score to notify
    NOTIFICATION_INCLUDE_RESPONSE: bool = True  # Include AI response in email

    # Pagination
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100

    # Caching
    CACHE_TTL: int = 3600
    CACHE_ENABLED: bool = True

    # Feature Flags
    ENABLE_WEBSOCKETS: bool = True
    ENABLE_BACKGROUND_JOBS: bool = True
    ENABLE_NOTIFICATIONS: bool = False

    # Health Checks
    HEALTH_CHECK_INTERVAL: int = 30
    HEALTH_CHECK_TIMEOUT: int = 5

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def build_database_url(cls, v: str | None, info) -> str | None:
        """Build database URL for async driver if needed."""
        if v and "postgresql://" in v and "asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: str | list[str]) -> list[str]:
        """Parse allowed hosts from comma-separated string or list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENV == "development"

    @property
    def is_testing(self) -> bool:
        """Check if running tests."""
        return self.ENV == "test"

    @property
    def is_lite_mode(self) -> bool:
        """Check if running in lite mode (no DB/Redis/Celery)."""
        return not self.DATABASE_URL or not self.REDIS_URL


# Create global settings instance
settings = Settings()
