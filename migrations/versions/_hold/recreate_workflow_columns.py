"""Recreate workflow columns

Revision ID: recreate_workflow_columns
Revises: fix_workflow_enum
Create Date: 2025-04-24 14:40:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "recreate_workflow_columns"
down_revision = "fix_workflow_enum"
branch_labels = None
depends_on = None


def upgrade():
    # Add the columns back with NOT NULL constraint
    op.add_column(
        "workflow_status",
        sa.Column(
            "current_stage",
            sa.Enum(
                "idea",
                "research",
                "outlining",
                "authoring",
                "images",
                "metadata",
                "review",
                "publishing",
                "updates",
                "syndication",
                name="workflowstage",
            ),
            nullable=False,
        ),
    )
    op.add_column(
        "workflow_status_history",
        sa.Column(
            "from_stage",
            sa.Enum(
                "idea",
                "research",
                "outlining",
                "authoring",
                "images",
                "metadata",
                "review",
                "publishing",
                "updates",
                "syndication",
                name="workflowstage",
            ),
            nullable=False,
        ),
    )
    op.add_column(
        "workflow_status_history",
        sa.Column(
            "to_stage",
            sa.Enum(
                "idea",
                "research",
                "outlining",
                "authoring",
                "images",
                "metadata",
                "review",
                "publishing",
                "updates",
                "syndication",
                name="workflowstage",
            ),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_column("workflow_status", "current_stage")
    op.drop_column("workflow_status_history", "from_stage")
    op.drop_column("workflow_status_history", "to_stage")
