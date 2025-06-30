"""post section enhancements

Revision ID: post_section_enhancements
Revises: 2f7ffc3d16bd
Create Date: 2025-04-22 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = 'post_section_enhancements'
down_revision = '2f7ffc3d16bd'
branch_labels = None
depends_on = None

def upgrade():
    # Create enum for content types
    op.create_table('post_section',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('post_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('subtitle', sa.String(length=200), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('image_id', sa.Integer(), nullable=True),
        sa.Column('video_url', sa.String(length=500), nullable=True),
        sa.Column('audio_url', sa.String(length=500), nullable=True),
        sa.Column('content_type', sa.String(length=50), nullable=False, server_default='text'),
        sa.Column('duration', sa.Integer(), nullable=True),  # Duration in seconds for video/audio content
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('social_media_snippets', sa.JSON(), nullable=True),
        sa.Column('section_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['post_id'], ['post.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['image_id'], ['image.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_post_section_position', 'post_id', 'position', unique=True)
    )

    # Add indexes for common queries
    op.create_index('idx_post_section_content_type', 'post_section', ['content_type'])
    op.create_index('idx_post_section_created', 'post_section', ['created_at'])

def downgrade():
    op.drop_index('idx_post_section_content_type')
    op.drop_index('idx_post_section_created')
    op.drop_table('post_section') 