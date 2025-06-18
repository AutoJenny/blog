"""add header_image_id column to post table

Revision ID: add_header_image_id
Revises: efac860d32a9
Create Date: 2025-04-24 11:16:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_header_image_id"
down_revision = "efac860d32a9"
branch_labels = None
depends_on = None


def upgrade():
    # Add header_image_id column to post table
    op.add_column("post", sa.Column("header_image_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_post_header_image_id", "post", "image", ["header_image_id"], ["id"]
    )


def downgrade():
    # Remove header_image_id column from post table
    op.drop_constraint("fk_post_header_image_id", "post", type_="foreignkey")
    op.drop_column("post", "header_image_id")
