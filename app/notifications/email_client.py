"""
Email client for sending opportunity notifications.

Sends HTML emails with opportunity details and AI-generated responses.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import structlog

from app.core.config import settings
from app.core.exceptions import ConfigurationError
from app.notifications.models import DailySummaryEmail, OpportunityEmail

logger = structlog.get_logger(__name__)


class EmailClient:
    """Client for sending emails via SMTP."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        use_tls: Optional[bool] = None,
    ):
        """
        Initialize email client.

        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_username: SMTP authentication username
            smtp_password: SMTP authentication password
            from_email: Sender email address
            use_tls: Whether to use TLS encryption
        """
        self.smtp_host = smtp_host or settings.SMTP_HOST
        self.smtp_port = smtp_port or settings.SMTP_PORT
        self.smtp_username = smtp_username or settings.SMTP_USERNAME
        self.smtp_password = smtp_password or settings.SMTP_PASSWORD
        self.from_email = from_email or settings.SMTP_FROM_EMAIL
        self.use_tls = use_tls if use_tls is not None else settings.SMTP_USE_TLS

        # Validate configuration
        if not all([self.smtp_host, self.smtp_port, self.from_email]):
            raise ConfigurationError(
                "Email client requires SMTP_HOST, SMTP_PORT, and SMTP_FROM_EMAIL configuration"
            )

        logger.info(
            "email_client_initialized",
            smtp_host=self.smtp_host,
            smtp_port=self.smtp_port,
            from_email=self.from_email,
        )

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Send email.

        Args:
            to: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text fallback (optional)

        Returns:
            bool: True if sent successfully

        Raises:
            Exception: If email sending fails
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to

            # Add text version if provided
            if text_body:
                msg.attach(MIMEText(text_body, "plain"))

            # Add HTML version
            msg.attach(MIMEText(html_body, "html"))

            # Connect and send
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            # Authenticate if credentials provided
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            # Send
            server.send_message(msg)
            server.quit()

            logger.info(
                "email_sent_successfully",
                to=to,
                subject=subject,
            )
            return True

        except Exception as e:
            logger.error(
                "email_send_failed",
                to=to,
                subject=subject,
                error=str(e),
                exc_info=True,
            )
            raise

    async def send_opportunity_email(self, email_data: OpportunityEmail) -> bool:
        """
        Send opportunity notification email.

        Args:
            email_data: Email data including opportunity details

        Returns:
            bool: True if sent successfully
        """
        from app.notifications.templates import render_opportunity_email

        # Render HTML template
        html_body = render_opportunity_email(email_data)

        # Create plain text fallback
        text_body = self._create_text_fallback(email_data)

        # Send email
        return await self.send_email(
            to=email_data.to,
            subject=email_data.subject,
            html_body=html_body,
            text_body=text_body,
        )

    async def send_daily_summary_email(self, email_data: DailySummaryEmail) -> bool:
        """
        Send daily summary notification email.

        Args:
            email_data: Email data including list of opportunities

        Returns:
            bool: True if sent successfully
        """
        from app.notifications.templates import render_daily_summary_email

        # Render HTML template
        html_body = render_daily_summary_email(email_data)

        # Create plain text fallback
        text_body = self._create_daily_summary_text_fallback(email_data)

        # Send email
        return await self.send_email(
            to=email_data.to,
            subject=email_data.subject,
            html_body=html_body,
            text_body=text_body,
        )

    def _create_text_fallback(self, email_data: OpportunityEmail) -> str:
        """
        Create plain text version of email.

        Args:
            email_data: Email data

        Returns:
            str: Plain text email body
        """
        lines = [
            f"New LinkedIn Opportunity - Tier {email_data.tier}",
            "",
            f"From: {email_data.recruiter_name}",
            f"Company: {email_data.company}",
            f"Position: {email_data.position}",
            f"Score: {email_data.total_score}/100",
            f"Salary: {email_data.salary_range}",
            "",
            "Tech Stack:",
            ", ".join(email_data.tech_stack),
            "",
        ]

        if email_data.suggested_response:
            lines.extend([
                "Suggested Response:",
                email_data.suggested_response,
                "",
            ])

        # Add action URLs
        if email_data.approve_url:
            lines.append(f"Approve: {email_data.approve_url}")
        if email_data.edit_url:
            lines.append(f"Edit: {email_data.edit_url}")
        if email_data.decline_url:
            lines.append(f"Decline: {email_data.decline_url}")

        return "\n".join(lines)

    def _create_daily_summary_text_fallback(self, email_data: DailySummaryEmail) -> str:
        """
        Create plain text version of daily summary email.

        Args:
            email_data: Daily summary email data

        Returns:
            str: Plain text email body
        """
        lines = [
            f"Daily LinkedIn Summary - {email_data.date}",
            f"{email_data.total_count} new opportunities",
            "",
            "=" * 60,
            "",
        ]

        for i, opp in enumerate(email_data.opportunities, 1):
            # Format salary
            if opp.salary_min and opp.salary_max:
                salary = f"{opp.currency}{opp.salary_min:,} - {opp.currency}{opp.salary_max:,}"
            elif opp.salary_min:
                salary = f"{opp.currency}{opp.salary_min:,}+"
            else:
                salary = "Not specified"

            lines.extend([
                f"Opportunity #{i} - {opp.tier} (Score: {opp.total_score}/100)",
                "-" * 60,
                f"From: {opp.recruiter_name}",
                f"Company: {opp.company or 'Unknown'}",
                f"Position: {opp.role or 'Unknown'}",
                f"Salary: {salary}",
                f"Tech Stack: {', '.join(opp.tech_stack or [])}",
                "",
            ])

            if opp.ai_response:
                response_preview = opp.ai_response
                if len(response_preview) > 300:
                    response_preview = response_preview[:297] + "..."
                lines.extend([
                    "Suggested Response:",
                    response_preview,
                    "",
                ])

            lines.append("")

        lines.extend([
            "=" * 60,
            "",
            "LinkedIn AI Agent - Daily Summary",
        ])

        return "\n".join(lines)


# Convenience function
async def send_opportunity_email(email_data: OpportunityEmail) -> bool:
    """
    Send opportunity notification email.

    Args:
        email_data: Email data

    Returns:
        bool: True if sent successfully
    """
    client = EmailClient()
    return await client.send_opportunity_email(email_data)
