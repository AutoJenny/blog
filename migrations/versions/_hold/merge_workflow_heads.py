"""merge workflow heads

Revision ID: merge_workflow_heads
Revises: update_workflow_stages, add_prompt_template
Create Date: 2025-04-24 19:38:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "merge_workflow_heads"
down_revision = ("update_workflow_stages", "add_prompt_template")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
