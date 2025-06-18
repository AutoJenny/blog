"""merge all heads

Revision ID: merge_all_heads
Revises: cfb806ae65e9, merge_workflow_heads, rename_provider_secret_to_auth_token
Create Date: 2025-04-24 19:39:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "merge_all_heads"
down_revision = (
    "cfb806ae65e9",
    "merge_workflow_heads",
    "rename_provider_secret_to_auth_token",
)
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
