"""
Celery application configuration.

This module initializes and configures the Celery application for
background job processing.
"""

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create Celery application
celery_app = Celery(
    "linkedin_agent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery Configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={"master_name": "mymaster"},
    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    worker_disable_rate_limits=False,
    # Task execution settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Reject task if worker dies
    task_track_started=True,  # Track when task starts
    # Task routing
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3},
    task_retry_backoff=True,
    task_retry_backoff_max=600,  # Max 10 minutes
    task_retry_jitter=True,
    # Rate limits
    task_annotations={
        "app.tasks.scraping_tasks.scrape_linkedin_messages": {
            "rate_limit": "10/m"  # Max 10 scraping tasks per minute
        },
        "app.tasks.processing_tasks.process_message": {
            "rate_limit": "50/m"  # Max 50 processing tasks per minute
        },
    },
)

# Define queues
celery_app.conf.task_queues = (
    # Default queue
    Queue("default", Exchange("default"), routing_key="default"),
    # High priority queue for urgent tasks
    Queue(
        "high_priority",
        Exchange("high_priority"),
        routing_key="high_priority",
        priority=10,
    ),
    # Scraping queue with rate limiting
    Queue("scraping", Exchange("scraping"), routing_key="scraping"),
    # Processing queue for DSPy pipeline
    Queue("processing", Exchange("processing"), routing_key="processing"),
    # Low priority queue for cleanup tasks
    Queue("low_priority", Exchange("low_priority"), routing_key="low_priority", priority=1),
)

# Route tasks to specific queues
celery_app.conf.task_routes = {
    "app.tasks.scraping_tasks.scrape_linkedin_messages": {"queue": "scraping"},
    "app.tasks.scraping_tasks.scrape_unread_messages": {"queue": "scraping"},
    "app.tasks.processing_tasks.process_message": {"queue": "processing"},
    "app.tasks.processing_tasks.process_opportunity": {"queue": "processing"},
    "app.tasks.processing_tasks.cleanup_old_opportunities": {"queue": "low_priority"},
}

# Periodic tasks (scheduled jobs)
celery_app.conf.beat_schedule = {
    # Scrape LinkedIn messages daily at 9 AM
    "scrape-and-summarize-daily": {
        "task": "app.tasks.scraping_tasks.scrape_and_send_daily_summary",
        "schedule": crontab(hour=9, minute=0),  # Daily at 9:00 AM
        "options": {"queue": "scraping"},
    },
    # Cleanup old opportunities daily at 2 AM
    "cleanup-opportunities-daily": {
        "task": "app.tasks.processing_tasks.cleanup_old_opportunities",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2:00 AM
        "options": {"queue": "low_priority"},
    },
}

# Auto-discover tasks in modules
celery_app.autodiscover_tasks(
    [
        "app.tasks.scraping_tasks",
        "app.tasks.processing_tasks",
        "app.tasks.monitoring_tasks",
    ]
)


# Celery signals
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks after Celery is configured."""
    logger.info("celery_periodic_tasks_configured")


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    logger.info("debug_task_executed", request=self.request)
    return f"Request: {self.request!r}"


# Celery startup/shutdown hooks
@celery_app.on_after_finalize.connect
def on_startup(sender, **kwargs):
    """Called when Celery app is finalized."""
    logger.info(
        "celery_app_started",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )


def create_celery_app() -> Celery:
    """
    Create and return Celery app instance.

    Returns:
        Configured Celery application
    """
    return celery_app
