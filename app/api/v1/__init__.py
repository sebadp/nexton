"""
API v1 Router - Combines all v1 endpoints.
"""
from fastapi import APIRouter

from app.api.v1 import health, metrics, opportunities, responses, profile, settings, scraping

# Create v1 router
router = APIRouter(prefix="/api/v1")

# Include sub-routers
router.include_router(health.router)
router.include_router(metrics.router)
router.include_router(opportunities.router)
router.include_router(responses.router)
router.include_router(profile.router)
router.include_router(settings.router)
router.include_router(scraping.router)