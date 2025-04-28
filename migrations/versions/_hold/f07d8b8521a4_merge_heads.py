"""merge heads

Revision ID: f07d8b8521a4
Revises: a494479e5ce4, add_post_fields
Create Date: 2025-04-23 16:43:31.301767

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f07d8b8521a4'
down_revision = ('a494479e5ce4', 'add_post_fields')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
