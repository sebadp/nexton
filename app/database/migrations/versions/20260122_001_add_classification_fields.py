"""Add conversation classification fields to opportunities.

Revision ID: 001_add_classification
Revises:
Create Date: 2026-01-22

Adds:
- conversation_state: NEW_OPPORTUNITY, FOLLOW_UP, COURTESY_CLOSE
- processing_status: processed, ignored, declined, manual_review, auto_responded
- requires_manual_review: boolean flag
- manual_review_reason: text explanation
- hard_filter_results: JSON for filter check results
- follow_up_analysis: JSON for follow-up message analysis
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_add_classification"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new classification columns to opportunities table."""
    # Add conversation_state column
    op.add_column(
        "opportunities",
        sa.Column(
            "conversation_state",
            sa.String(50),
            nullable=True,
            comment="NEW_OPPORTUNITY, FOLLOW_UP, COURTESY_CLOSE",
        ),
    )

    # Add processing_status column
    op.add_column(
        "opportunities",
        sa.Column(
            "processing_status",
            sa.String(50),
            nullable=True,
            comment="processed, ignored, declined, manual_review, auto_responded",
        ),
    )

    # Add requires_manual_review column
    op.add_column(
        "opportunities",
        sa.Column(
            "requires_manual_review",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    # Add manual_review_reason column
    op.add_column(
        "opportunities",
        sa.Column(
            "manual_review_reason",
            sa.Text(),
            nullable=True,
            comment="Reason why manual review is required",
        ),
    )

    # Add hard_filter_results column (JSON)
    op.add_column(
        "opportunities",
        sa.Column(
            "hard_filter_results",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
            comment="Results from hard filter checks",
        ),
    )

    # Add follow_up_analysis column (JSON)
    op.add_column(
        "opportunities",
        sa.Column(
            "follow_up_analysis",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
            comment="Analysis for follow-up messages",
        ),
    )

    # Create indexes for the new columns
    op.create_index(
        "idx_opportunities_manual_review",
        "opportunities",
        ["requires_manual_review"],
    )
    op.create_index(
        "idx_opportunities_conversation_state",
        "opportunities",
        ["conversation_state"],
    )
    op.create_index(
        "idx_opportunities_processing_status",
        "opportunities",
        ["processing_status"],
    )


def downgrade() -> None:
    """Remove classification columns from opportunities table."""
    # Drop indexes
    op.drop_index("idx_opportunities_processing_status", table_name="opportunities")
    op.drop_index("idx_opportunities_conversation_state", table_name="opportunities")
    op.drop_index("idx_opportunities_manual_review", table_name="opportunities")

    # Drop columns
    op.drop_column("opportunities", "follow_up_analysis")
    op.drop_column("opportunities", "hard_filter_results")
    op.drop_column("opportunities", "manual_review_reason")
    op.drop_column("opportunities", "requires_manual_review")
    op.drop_column("opportunities", "processing_status")
    op.drop_column("opportunities", "conversation_state")
