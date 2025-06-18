"""Fix post id sequence

Revision ID: fix_post_sequence
Revises: 12508c133a42
Create Date: 2025-04-24 14:27:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "fix_post_sequence"
down_revision = "12508c133a42"
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing sequence if it exists
    op.execute("DROP SEQUENCE IF EXISTS post_id_seq")

    # Create new sequence
    op.execute("CREATE SEQUENCE post_id_seq START 1")

    # Set the sequence ownership
    op.execute("ALTER SEQUENCE post_id_seq OWNED BY post.id")

    # Set the default value for the id column
    op.execute("ALTER TABLE post ALTER COLUMN id SET DEFAULT nextval('post_id_seq')")

    # Update the sequence's current value based on existing data
    op.execute(
        """
        SELECT setval('post_id_seq', COALESCE((SELECT MAX(id) FROM post), 0) + 1, false)
    """
    )


def downgrade():
    op.execute("ALTER TABLE post ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS post_id_seq")
