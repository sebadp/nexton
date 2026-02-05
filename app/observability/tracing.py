"""
OpenTelemetry tracing configuration.

Provides distributed tracing setup with automatic instrumentation for
FastAPI, SQLAlchemy, Redis, and custom spans for DSPy operations.
"""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def setup_tracing(app=None) -> None:
    """
    Setup OpenTelemetry tracing with automatic instrumentation.

    Args:
        app: Optional FastAPI application instance for instrumentation
    """
    if not settings.OTEL_ENABLED:
        logger.info("opentelemetry_disabled")
        return

    try:
        # Create resource with service information
        resource = Resource.create(
            {
                "service.name": settings.OTEL_SERVICE_NAME,
                "service.version": "1.0.0",
                "deployment.environment": settings.ENV,
            }
        )

        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)

        # Add OTLP exporter (for Jaeger/Tempo)
        if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
            otlp_exporter = OTLPSpanExporter(
                endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
                insecure=settings.ENV == "development",
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            logger.info(
                "otlp_exporter_configured",
                endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            )

        # Add console exporter for development
        if settings.ENV == "development":
            console_exporter = ConsoleSpanExporter()
            tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.info("console_exporter_configured")

        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)

        # Instrument FastAPI
        if app:
            FastAPIInstrumentor.instrument_app(
                app,
                excluded_urls=settings.OTEL_EXCLUDED_URLS,
                tracer_provider=tracer_provider,
            )
            logger.info("fastapi_instrumented")

        # Instrument SQLAlchemy
        SQLAlchemyInstrumentor().instrument(
            tracer_provider=tracer_provider,
            enable_commenter=True,
        )
        logger.info("sqlalchemy_instrumented")

        # Instrument Redis
        RedisInstrumentor().instrument(tracer_provider=tracer_provider)
        logger.info("redis_instrumented")

        logger.info(
            "opentelemetry_initialized",
            service_name=settings.OTEL_SERVICE_NAME,
            environment=settings.ENV,
        )

    except Exception as e:
        logger.error("opentelemetry_setup_failed", error=str(e))
        # Don't fail application startup if tracing fails
        raise


def get_tracer(name: str) -> trace.Tracer:
    """
    Get a tracer instance for custom instrumentation.

    Args:
        name: Tracer name (typically module name)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


class TracingContext:
    """
    Context manager for custom tracing spans.

    Example:
        with TracingContext("pipeline.forward", {"message_length": 100}):
            # Your code here
            result = pipeline.forward(...)
    """

    def __init__(
        self,
        span_name: str,
        attributes: dict | None = None,
        tracer_name: str = "app.custom",
    ):
        """
        Initialize tracing context.

        Args:
            span_name: Name of the span
            attributes: Optional span attributes
            tracer_name: Tracer name (default: app.custom)
        """
        self.span_name = span_name
        self.attributes = attributes or {}
        self.tracer = get_tracer(tracer_name)
        self.span: trace.Span | None = None

    def __enter__(self):
        """Start span."""
        self.span = self.tracer.start_span(self.span_name)

        # Set attributes
        for key, value in self.attributes.items():
            if value is not None:
                self.span.set_attribute(key, value)

        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End span and record exceptions."""
        if exc_type is not None and self.span:
            # Record exception
            self.span.record_exception(exc_val)
            self.span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_val)))

        if self.span:
            self.span.end()

        return False  # Don't suppress exceptions


def add_span_attributes(**attributes) -> None:
    """
    Add attributes to the current span.

    Args:
        **attributes: Key-value pairs to add as span attributes
    """
    span = trace.get_current_span()
    if span:
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)


def add_span_event(name: str, attributes: dict | None = None) -> None:
    """
    Add an event to the current span.

    Args:
        name: Event name
        attributes: Optional event attributes
    """
    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})


def set_span_error(error: Exception) -> None:
    """
    Record an error in the current span.

    Args:
        error: Exception to record
    """
    span = trace.get_current_span()
    if span:
        span.record_exception(error)
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))
