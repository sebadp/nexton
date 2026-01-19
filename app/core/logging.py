"""
Structured logging configuration using structlog.
"""
import logging
import sys
from typing import Any

import structlog
from structlog.stdlib import LoggerFactory

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure structured logging for the application.

    Uses structlog for structured JSON logging with:
    - ISO timestamps
    - Log levels
    - Context variables
    - Exception info
    - JSON output (for production/Loki)
    """

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Shared processors for all environments
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    # Development vs Production formatting
    if settings.is_development or settings.is_testing:
        # Pretty console output for development
        processors = shared_processors + [
            structlog.dev.set_exc_info,
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # JSON output for production (Loki/ELK)
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper())
        ),
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Structured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("user_logged_in", user_id=123, email="user@example.com")
    """
    return structlog.get_logger(name)


# Example usage context manager
class log_context:
    """
    Context manager for adding temporary context to logs.

    Example:
        with log_context(request_id="abc123", user_id=456):
            logger.info("processing_request")
            # All logs within this block will include request_id and user_id
    """

    def __init__(self, **kwargs):
        self.context = kwargs

    def __enter__(self):
        structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        structlog.contextvars.unbind_contextvars(*self.context.keys())


# Initialize logging on import
setup_logging()

# Create default logger
logger = get_logger(__name__)