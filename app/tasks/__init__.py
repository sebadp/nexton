"""
Celery tasks package.

This package contains all background tasks for the LinkedIn AI Agent.
"""

from app.tasks.celery_app import celery_app, create_celery_app

__all__ = ["celery_app", "create_celery_app"]
