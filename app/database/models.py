"""
Database models using SQLAlchemy ORM.
"""

from datetime import datetime

from sqlalchemy import (
    ARRAY,
    JSON,
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from app.database.base import Base


class Opportunity(Base):
    """
    Opportunity model representing a LinkedIn recruitment message.

    Stores all information extracted from recruiter messages,
    including scoring results and generated responses.
    """

    __tablename__ = "opportunities"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Recruiter Information
    recruiter_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Job Information
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tech_stack: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    # Compensation
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True, default="USD")

    # Work Arrangement
    remote_policy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Scoring & Classification
    total_score: Mapped[int | None] = mapped_column(
        Integer,
        CheckConstraint("total_score >= 0 AND total_score <= 100", name="check_score_range"),
        nullable=True,
    )
    tech_stack_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seniority_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    company_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    tier: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="HIGH_PRIORITY, INTERESANTE, POCO_INTERESANTE, NO_INTERESA",
    )

    # AI Response
    ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status Tracking
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="new",
        comment="new, processing, processed, error, archived",
    )

    # Conversation Classification (NEW)
    conversation_state: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="NEW_OPPORTUNITY, FOLLOW_UP, COURTESY_CLOSE",
    )
    processing_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="processed, ignored, declined, manual_review, auto_responded",
    )

    # Manual Review Tracking (NEW)
    requires_manual_review: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    manual_review_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reason why manual review is required",
    )

    # Hard Filter Results (NEW - JSON)
    hard_filter_results: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Results from hard filter checks (work_week, salary, tech_match, etc.)",
    )

    # Follow-up Analysis (NEW - JSON)
    follow_up_analysis: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Analysis for follow-up messages (question_type, can_auto_respond, etc.)",
    )

    # Raw Data
    raw_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    message_timestamp: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Original timestamp from LinkedIn message",
    )

    # Additional metadata
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index("idx_opportunities_tier", "tier"),
        Index("idx_opportunities_score", "total_score"),
        Index("idx_opportunities_created", "created_at"),
        Index("idx_opportunities_company", "company"),
        Index("idx_opportunities_status", "status"),
        Index("idx_opportunities_tier_score", "tier", "total_score"),  # Composite index
        Index("idx_opportunities_manual_review", "requires_manual_review"),
        Index("idx_opportunities_conversation_state", "conversation_state"),
        Index("idx_opportunities_processing_status", "processing_status"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Opportunity(id={self.id}, "
            f"company={self.company}, "
            f"role={self.role}, "
            f"score={self.total_score}, "
            f"tier={self.tier})>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "recruiter_name": self.recruiter_name,
            "company": self.company,
            "role": self.role,
            "seniority": self.seniority,
            "tech_stack": self.tech_stack,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "currency": self.currency,
            "remote_policy": self.remote_policy,
            "location": self.location,
            "total_score": self.total_score,
            "tech_stack_score": self.tech_stack_score,
            "salary_score": self.salary_score,
            "seniority_score": self.seniority_score,
            "company_score": self.company_score,
            "tier": self.tier,
            "ai_response": self.ai_response,
            "status": self.status,
            # New classification fields
            "conversation_state": self.conversation_state,
            "processing_status": self.processing_status,
            "requires_manual_review": self.requires_manual_review,
            "manual_review_reason": self.manual_review_reason,
            "hard_filter_results": self.hard_filter_results,
            "follow_up_analysis": self.follow_up_analysis,
            # Timestamps
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "message_timestamp": self.message_timestamp.isoformat()
            if self.message_timestamp
            else None,
            "processing_time_ms": self.processing_time_ms,
        }


class PendingResponse(Base):
    """
    Pending response model for tracking AI-generated responses awaiting approval.

    Stores responses that need user review before sending to LinkedIn.
    """

    __tablename__ = "pending_responses"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Key to Opportunity
    opportunity_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Response Content
    original_response: Mapped[str] = mapped_column(
        Text, nullable=False, comment="AI-generated response"
    )
    edited_response: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="User-edited response"
    )
    final_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Final response that was/will be sent",
    )

    # Status Tracking
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        comment="pending, approved, declined, sent, failed",
        index=True,
    )

    # User Actions
    approved_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    declined_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    # Error Tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    send_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    opportunity: Mapped["Opportunity"] = relationship(
        "Opportunity",
        backref=backref("pending_responses", passive_deletes=True),
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_pending_responses_status", "status"),
        Index("idx_pending_responses_created", "created_at"),
        Index("idx_pending_responses_opportunity", "opportunity_id", "status"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<PendingResponse(id={self.id}, "
            f"opportunity_id={self.opportunity_id}, "
            f"status={self.status})>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "original_response": self.original_response,
            "edited_response": self.edited_response,
            "final_response": self.final_response,
            "status": self.status,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "declined_at": self.declined_at.isoformat() if self.declined_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "error_message": self.error_message,
            "send_attempts": self.send_attempts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
