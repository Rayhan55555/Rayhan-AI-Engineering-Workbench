"""agent_executions

Revision ID: 002_agent_executions
Revises: 001_initial_schema
Create Date: 2026-11-04 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_agent_executions'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agent_executions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('agent_slug', sa.String(length=100), nullable=False),
        sa.Column('task_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Pending', nullable=False),
        sa.Column('scope', sa.String(length=50), server_default='read_only', nullable=False),
        sa.Column('instruction', sa.Text(), nullable=False),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('simulated', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['agent_slug'], ['agents.slug'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_executions_agent_slug'), 'agent_executions', ['agent_slug'], unique=False)
    op.create_index(op.f('ix_agent_executions_task_id'), 'agent_executions', ['task_id'], unique=False)
    op.create_index(op.f('ix_agent_executions_user_id'), 'agent_executions', ['user_id'], unique=False)
    op.create_index(op.f('ix_agent_executions_status'), 'agent_executions', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('agent_executions')
