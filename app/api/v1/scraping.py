"""
Scraping API endpoints for triggering and monitoring LinkedIn scraping.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/scraping", tags=["scraping"])


class ScrapingTriggerRequest(BaseModel):
    """Request to trigger scraping."""

    limit: int = 20
    unread_only: bool = True
    send_email: bool = False  # Disabled by default since we have frontend


class ScrapingTriggerResponse(BaseModel):
    """Response after triggering scraping."""

    task_id: str
    status: str
    message: str


class ScrapingStatusResponse(BaseModel):
    """Scraping status response."""

    is_running: bool
    last_run: str | None = None
    last_run_status: str | None = None
    last_run_count: int | None = None
    task_id: str | None = None
    task_status: str | None = None
    task_progress: dict | None = None


# In-memory store for last run info (in production, use Redis)
_scraping_state: dict[str, bool | str | int | None | dict] = {
    "is_running": False,
    "last_run": None,
    "last_run_status": None,
    "last_run_count": None,
    "current_task_id": None,
}


@router.post("/trigger", response_model=ScrapingTriggerResponse)
async def trigger_scraping(
    request: ScrapingTriggerRequest = ScrapingTriggerRequest(),
) -> ScrapingTriggerResponse:
    """
    Trigger LinkedIn message scraping.

    This will:
    1. Scrape unread messages from LinkedIn inbox
    2. Process each message through the DSPy pipeline
    3. Create opportunities in the database
    4. Optionally send email summary (disabled by default)

    In LITE_MODE, runs synchronously without Celery/Redis.
    """
    global _scraping_state

    from app.core.config import settings

    if _scraping_state["is_running"]:
        raise HTTPException(
            status_code=409,
            detail="Scraping is already in progress. Please wait for it to complete.",
        )

    # Check if running in lite mode
    if settings.LITE_MODE:
        return await _trigger_lite_mode_scraping(request)

    # Full mode: use Celery
    return await _trigger_full_mode_scraping(request)


async def _trigger_lite_mode_scraping(
    request: ScrapingTriggerRequest,
) -> ScrapingTriggerResponse:
    """Trigger scraping in lite mode (synchronous, no Celery)."""
    global _scraping_state

    from app.database.base import get_db
    from app.services.scraping_service import ScrapingService

    _scraping_state["is_running"] = True
    _scraping_state["current_task_id"] = "lite-mode-sync"

    try:
        # Get database session
        async for db in get_db():
            service = ScrapingService(db)
            result = await service.scrape_sync(
                limit=request.limit,
                unread_only=request.unread_only,
            )

            # Update state
            _scraping_state["is_running"] = False
            _scraping_state["last_run"] = datetime.utcnow().isoformat()
            _scraping_state["last_run_status"] = result.get("status", "unknown")
            _scraping_state["last_run_count"] = result.get("opportunities_created", 0)
            _scraping_state["current_task_id"] = None

            # Determine API status based on result
            api_status = result.get("status", "completed")
            if api_status == "success":
                api_status = "completed"
            elif api_status == "no_messages":
                api_status = "completed"
            elif api_status == "error":
                api_status = "failed"

            return ScrapingTriggerResponse(
                task_id="lite-mode-sync",
                status=api_status,
                message=result.get(
                    "message",
                    f"Scraping completado. Se crearon {result.get('opportunities_created', 0)} oportunidades.",
                ),
            )

        # Should not reach here
        raise HTTPException(status_code=500, detail="Failed to get database session")

    except Exception as e:
        _scraping_state["is_running"] = False
        _scraping_state["current_task_id"] = None
        raise HTTPException(status_code=500, detail=f"Lite mode scraping failed: {str(e)}") from e


async def _trigger_full_mode_scraping(
    request: ScrapingTriggerRequest,
) -> ScrapingTriggerResponse:
    """Trigger scraping in full mode (Celery background task)."""
    global _scraping_state

    try:
        from app.tasks.scraping_tasks import scrape_and_send_daily_summary, scrape_linkedin_messages

        _scraping_state["is_running"] = True
        _scraping_state["current_task_id"] = None

        if request.send_email:
            task = scrape_and_send_daily_summary.delay()
        else:
            task = scrape_linkedin_messages.delay(
                limit=request.limit, unread_only=request.unread_only
            )

        _scraping_state["current_task_id"] = task.id

        return ScrapingTriggerResponse(
            task_id=task.id,
            status="started",
            message=f"Scraping task started. Fetching up to {request.limit} {'unread ' if request.unread_only else ''}messages.",
        )

    except ImportError:
        _scraping_state["is_running"] = False
        raise HTTPException(
            status_code=503, detail="Celery not available. Check your configuration."
        ) from None
    except Exception as e:
        _scraping_state["is_running"] = False
        error_msg = str(e)
        if "Connection refused" in error_msg or "111" in error_msg:
            raise HTTPException(
                status_code=503, detail="Redis/Celery connection failed. Check your configuration."
            ) from None
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {error_msg}") from e


@router.get("/status", response_model=ScrapingStatusResponse)
async def get_scraping_status() -> ScrapingStatusResponse:
    """Get the current scraping status and last run info."""
    global _scraping_state

    task_status = None
    task_progress = None

    # Check if there's a running task
    if _scraping_state["current_task_id"]:
        try:
            from celery.result import AsyncResult

            from app.tasks.celery_app import celery_app

            result = AsyncResult(_scraping_state["current_task_id"], app=celery_app)
            task_status = result.status

            if result.ready():
                # Task completed
                _scraping_state["is_running"] = False
                _scraping_state["last_run"] = datetime.utcnow().isoformat()

                if result.successful():
                    task_result = result.result
                    _scraping_state["last_run_status"] = "success"
                    _scraping_state["last_run_count"] = (
                        task_result.get("processed_count", 0)
                        if isinstance(task_result, dict)
                        else 0
                    )
                else:
                    _scraping_state["last_run_status"] = "failed"
                    _scraping_state["last_run_count"] = 0

                _scraping_state["current_task_id"] = None

            elif result.state == "PROGRESS":
                task_progress = result.info

        except ImportError:
            pass
        except Exception:
            # If we can't check task status, assume it's done
            _scraping_state["is_running"] = False

    return ScrapingStatusResponse(
        is_running=_scraping_state["is_running"],
        last_run=_scraping_state["last_run"],
        last_run_status=_scraping_state["last_run_status"],
        last_run_count=_scraping_state["last_run_count"],
        task_id=_scraping_state["current_task_id"],
        task_status=task_status,
        task_progress=task_progress,
    )


@router.post("/cancel")
async def cancel_scraping() -> dict:
    """Cancel the current scraping task if running."""
    global _scraping_state

    if not _scraping_state["is_running"] or not _scraping_state["current_task_id"]:
        raise HTTPException(status_code=400, detail="No scraping task is currently running.")

    try:
        from celery.result import AsyncResult

        from app.tasks.celery_app import celery_app

        result = AsyncResult(_scraping_state["current_task_id"], app=celery_app)
        result.revoke(terminate=True)

        _scraping_state["is_running"] = False
        _scraping_state["current_task_id"] = None

        return {"status": "cancelled", "message": "Scraping task has been cancelled."}

    except ImportError:
        raise HTTPException(status_code=503, detail="Celery not available.") from None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}") from e
