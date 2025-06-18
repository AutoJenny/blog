"""add concept and description fields

Revision ID: add_post_fields
Revises: # will be filled in by alembic
Create Date: 2025-04-23 15:45:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_post_fields"  # will be replaced by alembic
down_revision = None  # will be replaced by alembic
branch_labels = None
depends_on = None


def upgrade():
    # Add description field to post table (concept already exists)
    op.add_column("post", sa.Column("description", sa.Text(), nullable=True))

    # Add is_conclusion flag to post_section
    op.add_column(
        "post_section",
        sa.Column(
            "is_conclusion", sa.Boolean(), nullable=False, server_default="false"
        ),
    )


def downgrade():
    # Remove the new columns
    op.drop_column("post", "description")
    op.drop_column("post_section", "is_conclusion")
