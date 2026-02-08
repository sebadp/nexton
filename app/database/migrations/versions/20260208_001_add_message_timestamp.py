"""Add message_timestamp to opportunities.

Revision ID: 002_add_message_timestamp
Revises: 001_add_classification
Create Date: 2026-02-08

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "002_add_message_timestamp"
down_revision = "001_add_classification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add message_timestamp column to opportunities table."""
    op.add_column(
        "opportunities",
        sa.Column(
            "message_timestamp",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="Original timestamp from LinkedIn message",
        ),
    )


def downgrade() -> None:
    """Remove message_timestamp column from opportunities table."""
    op.drop_column("opportunities", "message_timestamp")
