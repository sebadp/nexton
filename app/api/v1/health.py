"""
Health check endpoints.

Provides endpoints to check application and dependency health.
"""

import httpx
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.database.base import get_db

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health")
async def health_check() -> dict:
    """
    Basic health check endpoint.

    Returns:
        dict: Health status

    Status Codes:
        200: Application is healthy
    """
    return {"status": "healthy"}


@router.get("/health/live")
async def liveness_check() -> dict:
    """
    Kubernetes liveness probe endpoint.

    Checks if the application is alive and responsive.

    Returns:
        dict: Liveness status

    Status Codes:
        200: Application is alive
    """
    return {
        "status": "alive",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    Kubernetes readiness probe endpoint.

    Checks if the application is ready to accept traffic by verifying:
    - Database connectivity
    - Redis connectivity
    - Ollama availability

    Args:
        db: Database session

    Returns:
        JSONResponse: Readiness status with dependency checks

    Status Codes:
        200: Application is ready (all dependencies healthy)
        503: Application is not ready (one or more dependencies unhealthy)
    """
    checks = {
        "database": False,
        "redis": False,
    }

    # Check PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
        logger.debug("database_check", status="healthy")
    except Exception as e:
        logger.error("database_check", status="unhealthy", error=str(e))

    # Check Redis
    try:
        import redis.asyncio as aioredis

        # Check if Redis URL is configured
        if not settings.REDIS_URL:
            # If not configured, we consider it unavailable but don't raise an exception
            # This allows the app to start even if Redis is optional/missing
            checks["redis"] = False
            logger.warning("redis_check", status="unconfigured")
        else:
            redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await redis_client.ping()
            checks["redis"] = True
            await redis_client.close()
            logger.debug("redis_check", status="healthy")
    except Exception as e:
        logger.error("redis_check", status="unhealthy", error=str(e))

    # Check Ollama (only if using Ollama as LLM provider)
    if settings.LLM_PROVIDER == "ollama":
        checks["ollama"] = False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
                if response.status_code == 200:
                    checks["ollama"] = True
                    logger.debug("ollama_check", status="healthy")
                else:
                    logger.warning(
                        "ollama_check",
                        status="unhealthy",
                        status_code=response.status_code,
                    )
        except Exception as e:
            logger.error("ollama_check", status="unhealthy", error=str(e))

    # Determine overall status
    # In lite mode (no Redis configured), skip Redis from the required checks
    required_checks = {"database": checks["database"]}
    if settings.REDIS_URL:
        required_checks["redis"] = checks["redis"]
    if "ollama" in checks:
        required_checks["ollama"] = checks["ollama"]

    all_healthy = all(required_checks.values())
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    details = {
        "database": "PostgreSQL connection" if checks["database"] else "PostgreSQL unavailable",
        "redis": "Redis connection" if checks["redis"] else "Redis unavailable",
    }
    if "ollama" in checks:
        details["ollama"] = "Ollama API" if checks["ollama"] else "Ollama unavailable"

    response_data = {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "details": details,
    }

    logger.info(
        "readiness_check",
        status=response_data["status"],
        database=checks["database"],
        redis=checks["redis"],
        ollama=checks.get("ollama", "skipped"),
    )

    return JSONResponse(
        status_code=status_code,
        content=response_data,
    )


@router.get("/health/startup")
async def startup_check(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    Kubernetes startup probe endpoint.

    Checks if the application has started successfully.
    More lenient than readiness check - only requires database.

    Args:
        db: Database session

    Returns:
        JSONResponse: Startup status

    Status Codes:
        200: Application started successfully
        503: Application startup failed
    """
    try:
        await db.execute(text("SELECT 1"))
        logger.info("startup_check", status="started")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "started",
                "message": "Application started successfully",
            },
        )
    except Exception as e:
        logger.error("startup_check", status="failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "failed",
                "message": "Application startup failed",
                "error": str(e),
            },
        )
