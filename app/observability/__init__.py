"""
Observability module.

Provides distributed tracing, metrics, and monitoring capabilities.
"""

from app.observability.metrics import (
    get_metrics,
    setup_metrics,
    track_cache_operation,
    track_db_query,
    track_llm_call,
    track_llm_error,
    track_llm_request,
    track_opportunity_created,
    track_opportunity_processing_time,
    track_opportunity_score,
    track_pipeline_execution,
    update_opportunities_by_tier,
)
from app.observability.tracing import (
    TracingContext,
    add_span_attributes,
    add_span_event,
    get_tracer,
    set_span_error,
    setup_tracing,
)

# Langfuse LLM Observability (optional)
from app.observability.langfuse_setup import (
    setup_langfuse,
    is_langfuse_enabled,
    get_langfuse_client,
    trace_pipeline_execution as langfuse_trace_pipeline,
    score_current_trace,
    update_current_trace,
    flush_langfuse,
)

__all__ = [
    # Tracing
    "setup_tracing",
    "get_tracer",
    "TracingContext",
    "add_span_attributes",
    "add_span_event",
    "set_span_error",
    # Metrics
    "setup_metrics",
    "get_metrics",
    "track_opportunity_created",
    "track_opportunity_score",
    "track_opportunity_processing_time",
    "track_pipeline_execution",
    "track_llm_call",
    "track_llm_request",
    "track_llm_error",
    "track_cache_operation",
    "track_db_query",
    "update_opportunities_by_tier",
    # Langfuse (LLM Observability)
    "setup_langfuse",
    "is_langfuse_enabled",
    "get_langfuse_client",
    "langfuse_trace_pipeline",
    "score_current_trace",
    "update_current_trace",
    "flush_langfuse",
]

