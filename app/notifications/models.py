"""
Data models for notifications and response workflow.
"""

from dataclasses import dataclass


@dataclass
class NotificationRule:
    """
    Rules for when to send notifications.

    Controls which opportunities trigger email notifications.
    """

    enabled: bool = True
    tier_threshold: list[str] | None = None  # ["A", "B"]
    score_threshold: int | None = None  # Minimum score (e.g., 80)
    notify_email: str = ""  # Email address to notify
    include_response: bool = True  # Include AI-generated response in email

    def __post_init__(self):
        """Set defaults."""
        if self.tier_threshold is None:
            self.tier_threshold = ["A", "B"]  # Default: notify for A and B tier

    def should_notify(self, opportunity) -> bool:
        """
        Check if opportunity matches notification rules.

        Args:
            opportunity: Opportunity model instance

        Returns:
            bool: True if should send notification
        """
        if not self.enabled:
            return False

        # Check tier
        if self.tier_threshold is not None and opportunity.tier not in self.tier_threshold:
            return False

        # Check score threshold
        if self.score_threshold and opportunity.total_score < self.score_threshold:
            return False

        return True


@dataclass
class OpportunityEmail:
    """Email data for opportunity notification."""

    to: str
    subject: str
    opportunity_id: int
    recruiter_name: str
    company: str
    position: str
    tier: str
    total_score: int
    salary_range: str
    tech_stack: list[str]
    suggested_response: str | None = None
    # Action URLs
    approve_url: str | None = None
    edit_url: str | None = None
    decline_url: str | None = None


@dataclass
class DailySummaryEmail:
    """Email data for daily summary of all opportunities."""

    to: str
    subject: str
    opportunities: list  # List of Opportunity model instances
    total_count: int
    date: str  # Date of the summary


@dataclass
class LiteSummaryEmail:
    """Email data for lite mode summary (no database, uses OpportunityResult directly)."""

    to: str
    subject: str
    results: list  # List of OpportunityResult from pipeline
    total_count: int
    date: str  # Date of the summary
