"""update workflow stages

Revision ID: update_workflow_stages
Revises: efac860d32a9
Create Date: 2025-04-24 10:50:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "update_workflow_stages"
down_revision = "efac860d32a9"
branch_labels = None
depends_on = None

# Old and new enum values
old_values = (
    "conceptualization",
    "drafting",
    "editing",
    "review",
    "publishing",
    "published",
    "archived",
)
new_values = (
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
)

# Stage mapping for data migration
stage_mapping = {
    "conceptualization": "idea",
    "drafting": "authoring",
    "editing": "review",
    "review": "review",
    "publishing": "publishing",
    "published": "publishing",
    "archived": "publishing",
}


def upgrade():
    # Create new enum type
    op.execute("ALTER TYPE workflowstage RENAME TO workflowstage_old")
    op.execute(f"CREATE TYPE workflowstage AS ENUM {new_values}")

    # Update workflow_status table
    op.execute(
        """
        ALTER TABLE workflow_status 
        ALTER COLUMN current_stage TYPE workflowstage 
        USING current_stage::text::workflowstage
    """
    )

    # Update workflow_status_history table
    op.execute(
        """
        ALTER TABLE workflow_status_history 
        ALTER COLUMN from_stage TYPE workflowstage 
        USING from_stage::text::workflowstage
    """
    )
    op.execute(
        """
        ALTER TABLE workflow_status_history 
        ALTER COLUMN to_stage TYPE workflowstage 
        USING to_stage::text::workflowstage
    """
    )

    # Drop old enum type
    op.execute("DROP TYPE workflowstage_old")

    # Update existing records with new stage values
    for old_stage, new_stage in stage_mapping.items():
        op.execute(
            f"""
            UPDATE workflow_status 
            SET current_stage = '{new_stage}' 
            WHERE current_stage::text = '{old_stage}'
        """
        )
        op.execute(
            f"""
            UPDATE workflow_status_history 
            SET from_stage = '{new_stage}' 
            WHERE from_stage::text = '{old_stage}'
        """
        )
        op.execute(
            f"""
            UPDATE workflow_status_history 
            SET to_stage = '{new_stage}' 
            WHERE to_stage::text = '{old_stage}'
        """
        )


def downgrade():
    # Create old enum type
    op.execute("ALTER TYPE workflowstage RENAME TO workflowstage_new")
    op.execute(f"CREATE TYPE workflowstage AS ENUM {old_values}")

    # Revert workflow_status table
    op.execute(
        """
        ALTER TABLE workflow_status 
        ALTER COLUMN current_stage TYPE workflowstage 
        USING current_stage::text::workflowstage
    """
    )

    # Revert workflow_status_history table
    op.execute(
        """
        ALTER TABLE workflow_status_history 
        ALTER COLUMN from_stage TYPE workflowstage 
        USING from_stage::text::workflowstage
    """
    )
    op.execute(
        """
        ALTER TABLE workflow_status_history 
        ALTER COLUMN to_stage TYPE workflowstage 
        USING to_stage::text::workflowstage
    """
    )

    # Drop new enum type
    op.execute("DROP TYPE workflowstage_new")
