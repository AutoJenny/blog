"""rename provider_secret to auth_token

Revision ID: rename_provider_secret_to_auth_token
Revises: add_llm_config_table
Create Date: 2025-04-24 17:55:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "rename_provider_secret_to_auth_token"
down_revision = "add_llm_config_table"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "llm_config",
        "provider_secret",
        new_column_name="auth_token",
        existing_type=sa.String(length=200),
        existing_nullable=True,
    )


def downgrade():
    op.alter_column(
        "llm_config",
        "auth_token",
        new_column_name="provider_secret",
        existing_type=sa.String(length=200),
        existing_nullable=True,
    )
