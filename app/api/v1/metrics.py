"""
Metrics API endpoints.

Exposes Prometheus metrics for monitoring and alerting.
"""

from fastapi import APIRouter, Response

from app.observability import get_metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def metrics() -> Response:
    """
    Get Prometheus metrics.

    Returns:
        Prometheus metrics in text format
    """
    metrics_data = get_metrics()
    return Response(
        content=metrics_data,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
