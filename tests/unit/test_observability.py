"""
Unit tests for observability (tracing and metrics).
"""

from unittest.mock import MagicMock, patch

import pytest

from app.observability import (
    TracingContext,
    add_span_attributes,
    add_span_event,
    get_tracer,
    set_span_error,
    track_cache_operation,
    track_db_query,
    track_llm_call,
    track_opportunity_created,
    track_opportunity_processing_time,
    track_opportunity_score,
    track_pipeline_execution,
    update_opportunities_by_tier,
)
from app.observability.metrics import (
    cache_operations_total,
    db_queries_total,
    llm_api_calls_total,
    opportunities_by_tier,
    opportunities_created_total,
    opportunity_processing_time,
    opportunity_score_distribution,
    pipeline_executions_total,
)


class TestTracingContext:
    """Test TracingContext class."""

    @patch("app.observability.tracing.get_tracer")
    def test_context_manager_success(self, mock_get_tracer):
        """Test successful context manager execution."""
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = mock_span
        mock_get_tracer.return_value = mock_tracer

        with TracingContext("test.operation", {"attr": "value"}):
            pass

        mock_tracer.start_span.assert_called_once_with("test.operation")
        mock_span.set_attribute.assert_called_once_with("attr", "value")
        mock_span.end.assert_called_once()

    @patch("app.observability.tracing.get_tracer")
    def test_context_manager_with_exception(self, mock_get_tracer):
        """Test context manager with exception."""
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = mock_span
        mock_get_tracer.return_value = mock_tracer

        test_error = ValueError("Test error")

        with pytest.raises(ValueError):
            with TracingContext("test.operation"):
                raise test_error

        mock_span.record_exception.assert_called_once_with(test_error)
        mock_span.set_status.assert_called_once()
        mock_span.end.assert_called_once()

    @patch("app.observability.tracing.get_tracer")
    def test_context_with_none_attributes(self, mock_get_tracer):
        """Test that None attributes are not set."""
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = mock_span
        mock_get_tracer.return_value = mock_tracer

        with TracingContext("test.operation", {"attr1": "value", "attr2": None}):
            pass

        # Only non-None attributes should be set
        assert mock_span.set_attribute.call_count == 1


class TestTracingHelpers:
    """Test tracing helper functions."""

    @patch("app.observability.tracing.trace.get_current_span")
    def test_add_span_attributes(self, mock_get_span):
        """Test adding attributes to current span."""
        mock_span = MagicMock()
        mock_get_span.return_value = mock_span

        add_span_attributes(key1="value1", key2="value2")

        assert mock_span.set_attribute.call_count == 2

    @patch("app.observability.tracing.trace.get_current_span")
    def test_add_span_attributes_with_none(self, mock_get_span):
        """Test that None attributes are skipped."""
        mock_span = MagicMock()
        mock_get_span.return_value = mock_span

        add_span_attributes(key1="value", key2=None)

        assert mock_span.set_attribute.call_count == 1

    @patch("app.observability.tracing.trace.get_current_span")
    def test_add_span_event(self, mock_get_span):
        """Test adding event to current span."""
        mock_span = MagicMock()
        mock_get_span.return_value = mock_span

        add_span_event("test_event", {"detail": "info"})

        mock_span.add_event.assert_called_once_with("test_event", attributes={"detail": "info"})

    @patch("app.observability.tracing.trace.get_current_span")
    def test_set_span_error(self, mock_get_span):
        """Test recording error in span."""
        mock_span = MagicMock()
        mock_get_span.return_value = mock_span

        error = Exception("Test error")
        set_span_error(error)

        mock_span.record_exception.assert_called_once_with(error)
        mock_span.set_status.assert_called_once()


class TestMetricsTracking:
    """Test metrics tracking functions."""

    def test_track_opportunity_created(self):
        """Test opportunity creation tracking."""
        initial = opportunities_created_total.labels(tier="A", status="processed")._value.get()

        track_opportunity_created(tier="A", status="processed")

        final = opportunities_created_total.labels(tier="A", status="processed")._value.get()
        assert final > initial

    def test_track_opportunity_score(self):
        """Test opportunity score tracking."""
        initial_count = opportunity_score_distribution._sum.get()

        track_opportunity_score(85.5)

        final_count = opportunity_score_distribution._sum.get()
        assert final_count > initial_count

    def test_track_opportunity_processing_time(self):
        """Test processing time tracking."""
        initial_count = opportunity_processing_time._sum.get()

        track_opportunity_processing_time(1.5)

        final_count = opportunity_processing_time._sum.get()
        assert final_count > initial_count

    def test_track_pipeline_execution_success(self):
        """Test pipeline execution tracking."""
        initial = pipeline_executions_total.labels(status="success")._value.get()

        track_pipeline_execution("success", 2.5)

        final = pipeline_executions_total.labels(status="success")._value.get()
        assert final > initial

    def test_track_pipeline_execution_cached(self):
        """Test cached pipeline execution tracking."""
        initial = pipeline_executions_total.labels(status="cached")._value.get()

        track_pipeline_execution("cached", 0.0)

        final = pipeline_executions_total.labels(status="cached")._value.get()
        assert final > initial

    def test_track_llm_call(self):
        """Test LLM call tracking."""
        initial = llm_api_calls_total.labels(model="llama2", status="success")._value.get()

        track_llm_call(
            model="llama2",
            status="success",
            latency_seconds=1.2,
            tokens_used={"prompt": 100, "completion": 50},
        )

        final = llm_api_calls_total.labels(model="llama2", status="success")._value.get()
        assert final > initial

    def test_track_cache_operation(self):
        """Test cache operation tracking."""
        initial = cache_operations_total.labels(operation="get", status="hit")._value.get()

        track_cache_operation("get", "hit", 0.005)

        final = cache_operations_total.labels(operation="get", status="hit")._value.get()
        assert final > initial

    def test_track_db_query(self):
        """Test database query tracking."""
        initial = db_queries_total.labels(operation="select", table="opportunities")._value.get()

        track_db_query("select", "opportunities", 0.05)

        final = db_queries_total.labels(operation="select", table="opportunities")._value.get()
        assert final > initial

    def test_update_opportunities_by_tier(self):
        """Test updating opportunities by tier gauge."""
        tier_counts = {"A": 10, "B": 25, "C": 40, "D": 15}

        update_opportunities_by_tier(tier_counts)

        # Verify gauges are set
        assert opportunities_by_tier.labels(tier="A")._value.get() == 10
        assert opportunities_by_tier.labels(tier="B")._value.get() == 25
        assert opportunities_by_tier.labels(tier="C")._value.get() == 40
        assert opportunities_by_tier.labels(tier="D")._value.get() == 15


class TestMetricsEndpoint:
    """Test metrics endpoint."""

    @patch("app.observability.metrics.generate_latest")
    def test_get_metrics(self, mock_generate):
        """Test metrics generation."""
        from app.observability import get_metrics

        mock_generate.return_value = b"# HELP test metric\ntest_metric 1.0\n"

        result = get_metrics()

        assert result == b"# HELP test metric\ntest_metric 1.0\n"
        mock_generate.assert_called_once()


class TestSetupFunctions:
    """Test setup functions."""

    @patch("app.observability.tracing.trace.set_tracer_provider")
    @patch("app.observability.tracing.FastAPIInstrumentor")
    @patch("app.observability.tracing.SQLAlchemyInstrumentor")
    @patch("app.observability.tracing.RedisInstrumentor")
    def test_setup_tracing(
        self,
        mock_redis_inst,
        mock_sql_inst,
        mock_fastapi_inst,
        mock_set_provider,
    ):
        """Test tracing setup."""
        from app.observability import setup_tracing

        mock_app = MagicMock()

        with patch("app.observability.tracing.settings") as mock_settings:
            mock_settings.OTEL_ENABLED = True
            mock_settings.OTEL_SERVICE_NAME = "test-service"
            mock_settings.ENV = "test"
            mock_settings.OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4318"
            mock_settings.OTEL_EXCLUDED_URLS = "/health,/metrics"

            setup_tracing(mock_app)

            # Verify instrumentation was called
            mock_fastapi_inst.instrument_app.assert_called_once()
            mock_sql_inst.return_value.instrument.assert_called_once()
            mock_redis_inst.return_value.instrument.assert_called_once()

    @patch("app.observability.tracing.settings")
    def test_setup_tracing_disabled(self, mock_settings):
        """Test tracing setup when disabled."""
        from app.observability import setup_tracing

        mock_settings.OTEL_ENABLED = False

        # Should not raise exception
        setup_tracing(None)

    def test_setup_metrics(self):
        """Test metrics setup."""
        from app.observability import setup_metrics

        # Should initialize without errors
        setup_metrics()


class TestGetTracer:
    """Test tracer retrieval."""

    @patch("app.observability.tracing.trace.get_tracer")
    def test_get_tracer(self, mock_get_tracer):
        """Test getting tracer instance."""
        mock_tracer = MagicMock()
        mock_get_tracer.return_value = mock_tracer

        tracer = get_tracer("test.module")

        mock_get_tracer.assert_called_once_with("test.module")
        assert tracer == mock_tracer
