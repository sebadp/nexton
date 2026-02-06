"""
Notification service for sending opportunity alerts.

Handles email notifications when new opportunities are processed.
Supports both full mode (with DB models) and lite mode (with pipeline results).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import structlog

from app.core.config import settings
from app.notifications.email_client import EmailClient
from app.notifications.models import (
    DailySummaryEmail,
    LiteSummaryEmail,
    NotificationRule,
    OpportunityEmail,
)

# Conditional import for full mode (with database)
if TYPE_CHECKING:
    from app.database.models import Opportunity
    from app.dspy_modules.models import OpportunityResult

logger = structlog.get_logger(__name__)


class NotificationService:
    """Service for sending opportunity notifications."""

    def __init__(
        self,
        email_client: EmailClient | None = None,
        notification_rule: NotificationRule | None = None,
    ):
        """
        Initialize notification service.

        Args:
            email_client: Email client (creates default if not provided)
            notification_rule: Notification rules (uses settings if not provided)
        """
        self.email_client = email_client or EmailClient()

        # Load notification rules from settings
        if notification_rule is None:
            self.notification_rule = NotificationRule(
                enabled=settings.NOTIFICATION_ENABLED,
                tier_threshold=settings.NOTIFICATION_TIER_THRESHOLD,
                score_threshold=settings.NOTIFICATION_SCORE_THRESHOLD,
                notify_email=settings.NOTIFICATION_EMAIL,
                include_response=settings.NOTIFICATION_INCLUDE_RESPONSE,
            )
        else:
            self.notification_rule = notification_rule

        logger.info(
            "notification_service_initialized",
            enabled=self.notification_rule.enabled,
            tier_threshold=self.notification_rule.tier_threshold,
            score_threshold=self.notification_rule.score_threshold,
        )

    async def notify_opportunity(
        self,
        opportunity: Opportunity,
        base_url: str = "http://localhost:8000",
    ) -> bool:
        """
        Send notification for new opportunity.

        Args:
            opportunity: Opportunity to notify about
            base_url: Base URL for action links

        Returns:
            bool: True if notification was sent
        """
        # Check if notifications are enabled
        if not self.notification_rule.enabled:
            logger.debug("notifications_disabled", opportunity_id=opportunity.id)
            return False

        # Check if notification email is configured
        if not self.notification_rule.notify_email:
            logger.warning(
                "notification_email_not_configured",
                opportunity_id=opportunity.id,
            )
            return False

        # Check if opportunity should trigger notification
        if not self.notification_rule.should_notify(opportunity):
            logger.info(
                "opportunity_does_not_meet_notification_criteria",
                opportunity_id=opportunity.id,
                tier=opportunity.tier,
                score=opportunity.total_score,
            )
            return False

        try:
            # Build email data
            email_data = self._build_email_data(opportunity, base_url)

            # Send email
            await self.email_client.send_opportunity_email(email_data)

            logger.info(
                "opportunity_notification_sent",
                opportunity_id=opportunity.id,
                tier=opportunity.tier,
                score=opportunity.total_score,
                to=email_data.to,
            )

            return True

        except Exception as e:
            logger.error(
                "opportunity_notification_failed",
                opportunity_id=opportunity.id,
                error=str(e),
                exc_info=True,
            )
            return False

    async def send_daily_summary(
        self,
        opportunities: list[Opportunity],
    ) -> bool:
        """
        Send daily summary email with all new opportunities.

        Args:
            opportunities: List of opportunities to include in summary

        Returns:
            bool: True if notification was sent
        """
        # Check if notifications are enabled
        if not self.notification_rule.enabled:
            logger.debug("notifications_disabled")
            return False

        # Check if notification email is configured
        if not self.notification_rule.notify_email:
            logger.warning("notification_email_not_configured")
            return False

        # Check if there are any opportunities
        if not opportunities:
            logger.info("no_opportunities_to_send")
            return False

        try:
            # Build email data
            email_data = DailySummaryEmail(
                to=self.notification_rule.notify_email,
                subject=f"Daily LinkedIn Summary - {len(opportunities)} new opportunit{'y' if len(opportunities) == 1 else 'ies'}",
                opportunities=opportunities,
                total_count=len(opportunities),
                date=datetime.now().strftime("%B %d, %Y"),
            )

            # Send email
            await self.email_client.send_daily_summary_email(email_data)

            logger.info(
                "daily_summary_sent",
                opportunities_count=len(opportunities),
                to=email_data.to,
            )

            return True

        except Exception as e:
            logger.error(
                "daily_summary_failed",
                opportunities_count=len(opportunities),
                error=str(e),
                exc_info=True,
            )
            return False

    async def send_lite_summary(
        self,
        results: list[OpportunityResult],
    ) -> bool:
        """
        Send summary email for lite mode (no database).

        Works with OpportunityResult directly from pipeline, no DB models needed.

        Args:
            results: List of OpportunityResult from pipeline processing

        Returns:
            bool: True if notification was sent
        """
        # Check if notifications are enabled
        if not self.notification_rule.enabled:
            logger.debug("notifications_disabled")
            return False

        # Check if notification email is configured
        if not self.notification_rule.notify_email:
            logger.warning("notification_email_not_configured")
            return False

        # Filter results - only non-ignored messages
        valid_results = [r for r in results if r.status != "ignored"]

        # Check if there are any results
        if not valid_results:
            logger.info("no_results_to_send")
            return False

        try:
            # Build email data
            email_data = LiteSummaryEmail(
                to=self.notification_rule.notify_email,
                subject=f"LinkedIn Agent Lite - {len(valid_results)} message{'s' if len(valid_results) != 1 else ''} processed",
                results=valid_results,
                total_count=len(valid_results),
                date=datetime.now().strftime("%B %d, %Y"),
            )

            # Send email
            await self.email_client.send_lite_summary_email(email_data)

            logger.info(
                "lite_summary_sent",
                results_count=len(valid_results),
                to=email_data.to,
            )

            return True

        except Exception as e:
            logger.error(
                "lite_summary_failed",
                results_count=len(results),
                error=str(e),
                exc_info=True,
            )
            return False

    def _build_email_data(
        self,
        opportunity: Opportunity,
        base_url: str,
    ) -> OpportunityEmail:
        """
        Build email data from opportunity.

        Args:
            opportunity: Opportunity
            base_url: Base URL for action links

        Returns:
            OpportunityEmail: Email data
        """
        # Format salary range
        if opportunity.salary_min and opportunity.salary_max:
            salary_range = (
                f"{opportunity.currency}{opportunity.salary_min:,} - "
                f"{opportunity.currency}{opportunity.salary_max:,}"
            )
        elif opportunity.salary_min:
            salary_range = f"{opportunity.currency}{opportunity.salary_min:,}+"
        else:
            salary_range = "Not specified"

        # Build subject
        subject = (
            f"New {opportunity.tier}-Tier Opportunity: {opportunity.company} - {opportunity.role}"
        )

        # Include AI response if enabled
        suggested_response = None
        if self.notification_rule.include_response and opportunity.ai_response:
            suggested_response = opportunity.ai_response

        # Build action URLs
        approve_url = f"{base_url}/api/v1/responses/{opportunity.id}/approve"
        edit_url = f"{base_url}/api/v1/responses/{opportunity.id}/edit"
        decline_url = f"{base_url}/api/v1/responses/{opportunity.id}/decline"

        return OpportunityEmail(
            to=self.notification_rule.notify_email,
            subject=subject,
            opportunity_id=opportunity.id,
            recruiter_name=opportunity.recruiter_name,
            company=opportunity.company or "Unknown",
            position=opportunity.role or "Unknown",
            tier=opportunity.tier or "C",
            total_score=opportunity.total_score if opportunity.total_score is not None else 0,
            salary_range=salary_range,
            tech_stack=opportunity.tech_stack or [],
            suggested_response=suggested_response,
            approve_url=approve_url,
            edit_url=edit_url,
            decline_url=decline_url,
        )


# Convenience function
async def notify_opportunity(
    opportunity: Opportunity,
    base_url: str = "http://localhost:8000",
) -> bool:
    """
    Send notification for opportunity.

    Args:
        opportunity: Opportunity to notify about
        base_url: Base URL for action links

    Returns:
        bool: True if notification was sent
    """
    service = NotificationService()
    return await service.notify_opportunity(opportunity, base_url)
