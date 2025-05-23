"""Add normalized workflow stage and sub-stage tables

Revision ID: bb816b682766
Revises: 3856d3f55261
Create Date: 2025-04-26 14:45:46.687043

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bb816b682766'
down_revision = '3856d3f55261'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('workflow_stage_entity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('workflow_sub_stage_entity',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('stage_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['stage_id'], ['workflow_stage_entity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('post_workflow_stage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=True),
    sa.Column('stage_id', sa.Integer(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.ForeignKeyConstraint(['post_id'], ['post.id'], ),
    sa.ForeignKeyConstraint(['stage_id'], ['workflow_stage_entity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('post_workflow_sub_stage',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post_workflow_stage_id', sa.Integer(), nullable=True),
    sa.Column('sub_stage_id', sa.Integer(), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['post_workflow_stage_id'], ['post_workflow_stage.id'], ),
    sa.ForeignKeyConstraint(['sub_stage_id'], ['workflow_sub_stage_entity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('post_workflow_sub_stage')
    op.drop_table('post_workflow_stage')
    op.drop_table('workflow_sub_stage_entity')
    op.drop_table('workflow_stage_entity')
    # ### end Alembic commands ###
