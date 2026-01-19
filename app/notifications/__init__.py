"""
Notification system for LinkedIn opportunities.

Sends email notifications when high-value opportunities are detected.
"""

from app.notifications.email_client import EmailClient, send_opportunity_email
from app.notifications.models import DailySummaryEmail, NotificationRule, OpportunityEmail
from app.notifications.service import NotificationService, notify_opportunity
from app.notifications.templates import render_daily_summary_email, render_opportunity_email

__all__ = [
    "EmailClient",
    "send_opportunity_email",
    "NotificationRule",
    "OpportunityEmail",
    "DailySummaryEmail",
    "NotificationService",
    "notify_opportunity",
    "render_opportunity_email",
    "render_daily_summary_email",
]
