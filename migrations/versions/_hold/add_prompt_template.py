"""add prompt template table

Revision ID: add_prompt_template
Revises: recreate_workflow_columns
Create Date: 2025-04-24 17:57:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_prompt_template"
down_revision = "recreate_workflow_columns"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prompt_template",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("prompt_template")
