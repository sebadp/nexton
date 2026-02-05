"""
Celery tasks for sending LinkedIn messages.

Background tasks for handling approved response sending.
"""

import asyncio

from app.core.logging import get_logger
from app.database.database import async_session
from app.database.repositories import PendingResponseRepository
from app.services.linkedin_messenger import LinkedInResponseService
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="send_linkedin_response",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def send_linkedin_response(self, response_id: int):
    """
    Send an approved LinkedIn response.

    This task is queued when a user approves a response.
    It will send the message to LinkedIn and update the status.

    Args:
        response_id: ID of the pending response to send

    Returns:
        dict: Result with status and message
    """
    logger.info(
        "starting_linkedin_response_send_task", response_id=response_id, task_id=self.request.id
    )

    try:
        # Run the async send operation
        result = asyncio.run(_send_response_async(response_id))

        if result["success"]:
            logger.info(
                "linkedin_response_sent_successfully",
                response_id=response_id,
                task_id=self.request.id,
            )
        else:
            logger.error(
                "linkedin_response_send_failed",
                response_id=response_id,
                error=result.get("error"),
                task_id=self.request.id,
            )

            # Retry if failed
            raise self.retry(exc=Exception(result.get("error")))

        return result

    except Exception as e:
        logger.error(
            "linkedin_response_task_failed",
            response_id=response_id,
            error=str(e),
            task_id=self.request.id,
            exc_info=True,
        )

        # Retry with exponential backoff
        raise self.retry(exc=e) from e


async def _send_response_async(response_id: int) -> dict:
    """
    Async helper to send response.

    Args:
        response_id: Response ID

    Returns:
        dict: Result with success status
    """
    messenger_service = None

    try:
        # Get database session
        async with async_session() as db:
            repository = PendingResponseRepository(db)

            # Get pending response
            pending_response = await repository.get_by_id(response_id)

            if not pending_response:
                return {"success": False, "error": f"Response {response_id} not found"}

            if pending_response.status != "approved":
                return {
                    "success": False,
                    "error": f"Response {response_id} is not approved (status: {pending_response.status})",
                }

            # Create messenger service
            messenger_service = LinkedInResponseService()

            # Send the response
            success = await messenger_service.send_pending_response(pending_response, repository)

            # Commit database changes
            await db.commit()

            return {"success": success, "response_id": response_id}

    except Exception as e:
        logger.error(
            "send_response_async_failed", response_id=response_id, error=str(e), exc_info=True
        )
        return {"success": False, "error": str(e)}

    finally:
        # Cleanup messenger
        if messenger_service:
            try:
                await messenger_service.cleanup()
            except Exception as e:
                logger.warning("messenger_cleanup_failed", error=str(e))


@celery_app.task(name="send_multiple_linkedin_responses")
def send_multiple_linkedin_responses(response_ids: list[int]):
    """
    Send multiple LinkedIn responses.

    This is useful for batch processing approved responses.

    Args:
        response_ids: List of response IDs to send

    Returns:
        dict: Results for each response
    """
    logger.info("starting_batch_linkedin_response_send", count=len(response_ids))

    results = []
    for response_id in response_ids:
        try:
            result = send_linkedin_response.apply_async(args=[response_id])
            results.append({"response_id": response_id, "task_id": result.id, "status": "queued"})
        except Exception as e:
            logger.error("failed_to_queue_response", response_id=response_id, error=str(e))
            results.append({"response_id": response_id, "status": "error", "error": str(e)})

    logger.info("batch_linkedin_response_send_completed", total=len(response_ids), results=results)

    return {"total": len(response_ids), "results": results}
