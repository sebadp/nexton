"""
Prometheus metrics configuration.

Provides custom business metrics and instrumentation for monitoring
application performance, DSPy pipeline operations, and business KPIs.
"""

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ==========================================
# APPLICATION METRICS
# ==========================================

# Info metric for application version
app_info = Info("app", "Application information")
app_info.info(
    {
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
        "service_name": settings.APP_NAME,
    }
)

# ==========================================
# OPPORTUNITY METRICS
# ==========================================

# Counter for opportunities created
opportunities_created_total = Counter(
    "opportunities_created_total",
    "Total number of opportunities created",
    ["tier", "status"],
)

# Counter for opportunities by action
opportunities_action_total = Counter(
    "opportunities_action_total",
    "Total opportunities by action type",
    ["action"],  # create, update, delete, get
)

# Gauge for opportunities by tier
opportunities_by_tier = Gauge(
    "opportunities_by_tier",
    "Current number of opportunities by tier",
    ["tier"],
)

# Histogram for opportunity scores
opportunity_score_distribution = Histogram(
    "opportunity_score_distribution",
    "Distribution of opportunity scores",
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
)

# Histogram for opportunity processing time
opportunity_processing_time = Histogram(
    "opportunity_processing_time_seconds",
    "Time to process opportunities",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# ==========================================
# DSPY PIPELINE METRICS
# ==========================================

# Counter for pipeline executions
pipeline_executions_total = Counter(
    "dspy_pipeline_executions_total",
    "Total number of DSPy pipeline executions",
    ["status"],  # success, error, cached
)

# Histogram for pipeline execution time
pipeline_execution_time = Histogram(
    "dspy_pipeline_execution_time_seconds",
    "Time to execute DSPy pipeline",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0],
)

# Counter for LLM API calls
llm_api_calls_total = Counter(
    "llm_api_calls_total",
    "Total number of LLM API calls",
    ["model", "status"],
)

# Histogram for LLM API latency
llm_api_latency = Histogram(
    "llm_api_latency_seconds",
    "LLM API call latency",
    ["model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0],
)

# Counter for LLM API calls by provider
llm_provider_requests_total = Counter(
    "llm_provider_requests_total",
    "Total number of LLM provider API calls",
    ["provider", "model", "status"],  # provider: openai, anthropic, ollama; status: success, error
)

# Histogram for LLM provider latency
llm_provider_latency_seconds = Histogram(
    "llm_provider_latency_seconds",
    "LLM provider API call latency",
    ["provider", "model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# Counter for LLM tokens used
llm_tokens_used_total = Counter(
    "llm_tokens_used_total",
    "Total number of LLM tokens used",
    ["provider", "model", "type"],  # metric_type: prompt, completion
)

# Gauge for LLM cost
llm_cost_usd_total = Counter(
    "llm_cost_usd_total",
    "Total LLM cost in USD",
    ["provider", "model"],
)

# Counter for LLM errors by type
llm_errors_total = Counter(
    "llm_errors_total",
    "Total number of LLM errors",
    ["provider", "error_type"],  # error_type: rate_limit, timeout, auth, etc.
)

# ==========================================
# CACHE METRICS
# ==========================================

# Counter for cache operations
cache_operations_total = Counter(
    "cache_operations_total",
    "Total number of cache operations",
    ["operation", "status"],  # operation: get, set, delete; status: hit, miss, error
)

# Histogram for cache operation latency
cache_operation_latency = Histogram(
    "cache_operation_latency_seconds",
    "Cache operation latency",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
)

# Gauge for cache size
cache_size_bytes = Gauge(
    "cache_size_bytes",
    "Current size of cache in bytes",
    ["cache_type"],
)

# ==========================================
# DATABASE METRICS
# ==========================================

# Counter for database queries
db_queries_total = Counter(
    "db_queries_total",
    "Total number of database queries",
    ["operation", "table"],  # operation: select, insert, update, delete
)

# Histogram for database query latency
db_query_latency = Histogram(
    "db_query_latency_seconds",
    "Database query latency",
    ["operation", "table"],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)

# Gauge for database connection pool
db_connection_pool_size = Gauge(
    "db_connection_pool_size",
    "Database connection pool size",
    ["state"],  # state: active, idle, total
)

# ==========================================
# SCRAPER METRICS
# ==========================================

# Counter for scraping operations
scraper_operations_total = Counter(
    "scraper_operations_total",
    "Total number of scraping operations",
    ["operation", "status"],  # operation: login, fetch, parse
)

# Histogram for scraping latency
scraper_operation_latency = Histogram(
    "scraper_operation_latency_seconds",
    "Scraping operation latency",
    ["operation"],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)

# Counter for scraper errors
scraper_errors_total = Counter(
    "scraper_errors_total",
    "Total number of scraper errors",
    ["error_type"],
)

# ==========================================
# BUSINESS METRICS
# ==========================================

# Counter for tier assignments
tier_assignments_total = Counter(
    "tier_assignments_total",
    "Total number of opportunities assigned to each tier",
    ["tier"],
)

# Gauge for average score by company
company_average_score = Gauge(
    "company_average_score",
    "Average opportunity score by company",
    ["company"],
)

# Histogram for salary ranges
salary_range_distribution = Histogram(
    "salary_range_distribution_usd",
    "Distribution of salary ranges",
    buckets=[30000, 50000, 70000, 90000, 110000, 130000, 150000, 200000, 300000],
)

# ==========================================
# HELPER FUNCTIONS
# ==========================================


def track_opportunity_created(tier: str, status: str = "processed") -> None:
    """
    Track opportunity creation.

    Args:
        tier: Opportunity tier
        status: Opportunity status
    """
    opportunities_created_total.labels(tier=tier, status=status).inc()
    tier_assignments_total.labels(tier=tier).inc()


def track_opportunity_score(score: float) -> None:
    """
    Track opportunity score distribution.

    Args:
        score: Opportunity score
    """
    opportunity_score_distribution.observe(score)


def track_opportunity_processing_time(duration_seconds: float) -> None:
    """
    Track opportunity processing time.

    Args:
        duration_seconds: Processing time in seconds
    """
    opportunity_processing_time.observe(duration_seconds)


def track_pipeline_execution(status: str, duration_seconds: float) -> None:
    """
    Track DSPy pipeline execution.

    Args:
        status: Execution status (success, error, cached)
        duration_seconds: Execution time in seconds
    """
    pipeline_executions_total.labels(status=status).inc()
    if status != "cached":
        pipeline_execution_time.observe(duration_seconds)


def track_llm_call(
    model: str, status: str, latency_seconds: float, tokens_used: dict | None = None
) -> None:
    """
    Track LLM API call.

    Args:
        model: LLM model name
        status: Call status (success, error)
        latency_seconds: Call latency in seconds
        tokens_used: Optional dict with 'prompt' and 'completion' token counts
    """
    llm_api_calls_total.labels(model=model, status=status).inc()
    llm_api_latency.labels(model=model).observe(latency_seconds)

    if tokens_used:
        if "prompt" in tokens_used:
            llm_tokens_used_total.labels(model=model, type="prompt").inc(tokens_used["prompt"])
        if "completion" in tokens_used:
            llm_tokens_used_total.labels(model=model, type="completion").inc(
                tokens_used["completion"]
            )


def track_cache_operation(operation: str, status: str, latency_seconds: float) -> None:
    """
    Track cache operation.

    Args:
        operation: Operation type (get, set, delete)
        status: Operation status (hit, miss, error)
        latency_seconds: Operation latency in seconds
    """
    cache_operations_total.labels(operation=operation, status=status).inc()
    cache_operation_latency.labels(operation=operation).observe(latency_seconds)


def track_db_query(operation: str, table: str, latency_seconds: float) -> None:
    """
    Track database query.

    Args:
        operation: Query operation (select, insert, update, delete)
        table: Table name
        latency_seconds: Query latency in seconds
    """
    db_queries_total.labels(operation=operation, table=table).inc()
    db_query_latency.labels(operation=operation, table=table).observe(latency_seconds)


def update_opportunities_by_tier(tier_counts: dict) -> None:
    """
    Update opportunities by tier gauge.

    Args:
        tier_counts: Dictionary mapping tier to count
    """
    for tier, count in tier_counts.items():
        opportunities_by_tier.labels(tier=tier).set(count)


def get_metrics() -> bytes:
    """
    Get Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus text format
    """
    return bytes(generate_latest())


def track_llm_request(
    provider: str,
    model: str,
    status: str,
    duration_seconds: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost_usd: float = 0.0,
) -> None:
    """
    Track LLM provider request.

    Args:
        provider: Provider name (openai, anthropic, ollama)
        model: Model name
        status: Request status (success, error)
        duration_seconds: Request duration
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        cost_usd: Cost in USD
    """
    llm_provider_requests_total.labels(provider=provider, model=model, status=status).inc()
    llm_provider_latency_seconds.labels(provider=provider, model=model).observe(duration_seconds)

    if prompt_tokens > 0:
        llm_tokens_used_total.labels(provider=provider, model=model, type="prompt").inc(
            prompt_tokens
        )

    if completion_tokens > 0:
        llm_tokens_used_total.labels(provider=provider, model=model, type="completion").inc(
            completion_tokens
        )

    if cost_usd > 0:
        llm_cost_usd_total.labels(provider=provider, model=model).inc(cost_usd)


def track_llm_error(provider: str, error_type: str) -> None:
    """
    Track LLM provider error.

    Args:
        provider: Provider name
        error_type: Error type (rate_limit, timeout, auth, etc.)
    """
    llm_errors_total.labels(provider=provider, error_type=error_type).inc()


# ==========================================
# INITIALIZATION
# ==========================================


def setup_metrics() -> None:
    """Setup Prometheus metrics."""
    logger.info(
        "prometheus_metrics_initialized",
        service_name=settings.APP_NAME,
        environment=settings.ENV,
    )
