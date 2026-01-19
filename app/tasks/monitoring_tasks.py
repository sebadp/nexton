"""
Celery tasks for system monitoring and health checks.
"""

import asyncio
from typing import Dict

from sqlalchemy import text

from app.core.logging import get_logger
from app.database.base import AsyncSessionLocal as async_session
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.monitoring_tasks.health_check")
def health_check() -> Dict:
    """
    Periodic health check task.

    Checks:
    - Database connectivity
    - Redis connectivity (via Celery)
    - Basic system health

    Returns:
        Dictionary with health status
    """
    logger.info("running_health_check")

    health_status = {"status": "healthy", "checks": {}}

    # Check database
    try:
        async def check_db():
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
                return True

        db_healthy = asyncio.run(check_db())
        health_status["checks"]["database"] = "healthy" if db_healthy else "unhealthy"

    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"

    # Redis is implicitly healthy if Celery is working
    health_status["checks"]["redis"] = "healthy"
    health_status["checks"]["celery"] = "healthy"

    logger.info("health_check_completed", **health_status)

    return health_status


@celery_app.task(name="app.tasks.monitoring_tasks.ping")
def ping() -> str:
    """Simple ping task for testing Celery connectivity."""
    return "pong"
