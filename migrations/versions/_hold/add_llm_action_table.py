"""add llm_action table

Revision ID: add_llm_action_table
Revises: 
Create Date: 2025-04-28

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_llm_action_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'llm_action',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('field_name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('stage_name', sa.String(length=100), nullable=True),
        sa.Column('source_field', sa.String(length=100), nullable=False, server_default=''),
        sa.Column('prompt_template', sa.Text(), nullable=False),
        sa.Column('llm_model', sa.String(length=100), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False, default=0.7),
        sa.Column('max_tokens', sa.Integer(), nullable=False, default=64),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

def downgrade():
    op.drop_table('llm_action') 