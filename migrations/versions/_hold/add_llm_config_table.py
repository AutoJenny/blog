"""add llm config table

Revision ID: add_llm_config_table
Revises: fix_workflow_enum
Create Date: 2025-04-24 17:55:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_llm_config_table"
down_revision = "fix_workflow_enum"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "llm_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider_type", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("api_base", sa.String(length=200), nullable=False),
        sa.Column("provider_secret", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("llm_config")
