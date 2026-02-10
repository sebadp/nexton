"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langfuse import Langfuse

# Import routers
from app.api import v1
from app.core.config import settings
from app.core.exceptions import LinkedInAgentException, OpportunityNotFoundError
from app.core.logging import get_logger
from app.database.base import close_db, init_db
from app.observability import setup_metrics, setup_tracing

logger = get_logger(__name__)

# Initialize Langfuse client globally if needed for manual flushing
langfuse = Langfuse()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Startup:
    - Setup OpenTelemetry tracing
    - Initialize database (in development)
    - Log startup message

    Shutdown:
    - Close database connections
    - Log shutdown message
    """
    # Startup
    logger.info(
        "application_starting",
        env=settings.ENV,
        version=settings.APP_VERSION,
    )

    # Setup Prometheus metrics
    logger.info("initializing_prometheus_metrics")
    setup_metrics()

    # Setup OpenTelemetry tracing
    if settings.OTEL_ENABLED:
        logger.info("initializing_opentelemetry")
        setup_tracing(app)

    # Initialize database (only in development/test)
    if settings.is_development or settings.is_testing:
        logger.info("initializing_database")
        await init_db()

    yield

    # Shutdown
    logger.info("application_shutting_down")

    # Flush Langfuse traces
    if settings.LANGFUSE_SECRET_KEY:
        try:
            logger.info("flushing_langfuse_traces")
            langfuse.flush()
        except Exception as e:
            logger.error("langfuse_flush_failed", error=str(e))

    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready AI system for intelligent LinkedIn opportunity analysis",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(LinkedInAgentException)
async def linkedin_agent_exception_handler(
    request: Request,
    exc: LinkedInAgentException,
) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.error(
        "application_error",
        error=exc.message,
        details=exc.details,
        path=request.url.path,
    )

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(exc, OpportunityNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(
        "validation_error",
        errors=exc.errors(),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(
        "unexpected_error",
        error=str(exc),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.is_development else None,
        },
    )


# Include routers
app.include_router(v1.router)


# Root endpoint
@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
        "docs_url": "/docs" if settings.is_development else None,
    }


@app.get("/health")
async def health() -> dict:
    """Simple health check for Docker healthcheck."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
