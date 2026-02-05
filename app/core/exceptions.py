"""
Custom exception classes for the application.
"""


class LinkedInAgentException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(LinkedInAgentException):
    """Raised when database operations fail."""

    pass


class OpportunityNotFoundError(LinkedInAgentException):
    """Raised when an opportunity is not found in database."""

    pass


class LLMError(LinkedInAgentException):
    """Raised when LLM API calls fail."""

    pass


class OllamaConnectionError(LLMError):
    """Raised when cannot connect to Ollama."""

    pass


class ScraperError(LinkedInAgentException):
    """Raised when scraping operations fail."""

    pass


class LinkedInAuthError(ScraperError):
    """Raised when LinkedIn authentication fails."""

    pass


class RateLimitError(LinkedInAgentException):
    """Raised when rate limits are exceeded."""

    pass


class ValidationError(LinkedInAgentException):
    """Raised when data validation fails."""

    pass


class ConfigurationError(LinkedInAgentException):
    """Raised when configuration is invalid."""

    pass


class CacheError(LinkedInAgentException):
    """Raised when cache operations fail."""

    pass


class PipelineError(LinkedInAgentException):
    """Raised when DSPy pipeline execution fails."""

    pass
