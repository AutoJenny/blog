"""Fix workflow stage enum handling

Revision ID: fix_workflow_enum
Revises: fix_post_sequence
Create Date: 2025-04-24 14:33:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Enum
from app.models import WorkflowStage

# revision identifiers, used by Alembic.
revision = "fix_workflow_enum"
down_revision = "fix_post_sequence"
branch_labels = None
depends_on = None


def upgrade():
    # Drop the enum type and recreate it
    op.execute("DROP TYPE IF EXISTS workflowstage CASCADE")

    # Create new enum type with correct values
    values = [e.value for e in WorkflowStage]
    values_sql = ", ".join(f"'{v}'" for v in values)
    op.execute(f"CREATE TYPE workflowstage AS ENUM ({values_sql})")

    # Create temporary columns
    op.execute("ALTER TABLE workflow_status ADD COLUMN temp_stage text")
    op.execute("ALTER TABLE workflow_status_history ADD COLUMN temp_from text")
    op.execute("ALTER TABLE workflow_status_history ADD COLUMN temp_to text")

    # Copy data to temporary columns
    op.execute("UPDATE workflow_status SET temp_stage = current_stage::text")
    op.execute("UPDATE workflow_status_history SET temp_from = from_stage::text")
    op.execute("UPDATE workflow_status_history SET temp_to = to_stage::text")

    # Drop old columns
    op.execute("ALTER TABLE workflow_status DROP COLUMN current_stage")
    op.execute("ALTER TABLE workflow_status_history DROP COLUMN from_stage")
    op.execute("ALTER TABLE workflow_status_history DROP COLUMN to_stage")

    # Add new enum columns
    op.execute("ALTER TABLE workflow_status ADD COLUMN current_stage workflowstage")
    op.execute(
        "ALTER TABLE workflow_status_history ADD COLUMN from_stage workflowstage"
    )
    op.execute("ALTER TABLE workflow_status_history ADD COLUMN to_stage workflowstage")

    # Copy data back from temporary columns
    op.execute("UPDATE workflow_status SET current_stage = temp_stage::workflowstage")
    op.execute(
        "UPDATE workflow_status_history SET from_stage = temp_from::workflowstage"
    )
    op.execute("UPDATE workflow_status_history SET to_stage = temp_to::workflowstage")

    # Drop temporary columns
    op.execute("ALTER TABLE workflow_status DROP COLUMN temp_stage")
    op.execute("ALTER TABLE workflow_status_history DROP COLUMN temp_from")
    op.execute("ALTER TABLE workflow_status_history DROP COLUMN temp_to")

    # Set NOT NULL constraints
    op.execute("ALTER TABLE workflow_status ALTER COLUMN current_stage SET NOT NULL")
    op.execute(
        "ALTER TABLE workflow_status_history ALTER COLUMN from_stage SET NOT NULL"
    )
    op.execute("ALTER TABLE workflow_status_history ALTER COLUMN to_stage SET NOT NULL")


def downgrade():
    # No downgrade path needed as this is a fix
    pass
