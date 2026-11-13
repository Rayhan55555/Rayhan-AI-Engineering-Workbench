"""phase_12_13_content_portfolio

Revision ID: 004_phase_12_13_content_portfolio
Revises: 003_phases_07_to_11_tables
Create Date: 2026-11-12 23:46:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_phase_12_13_content_portfolio'
down_revision: Union[str, None] = '003_phases_07_to_11_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. content_items (Phase 12 Content Studio)
    op.create_table(
        'content_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=50), server_default='article', nullable=False),
        sa.Column('stage', sa.String(length=50), server_default='idea', nullable=False),
        sa.Column('channel', sa.String(length=50), server_default='blog', nullable=False),
        sa.Column('body_markdown', sa.Text(), server_default='', nullable=False),
        sa.Column('summary', sa.Text(), server_default='', nullable=False),
        sa.Column('rag_sources', sa.JSON(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_content_items_slug'), 'content_items', ['slug'], unique=True)
    op.create_index(op.f('ix_content_items_content_type'), 'content_items', ['content_type'], unique=False)
    op.create_index(op.f('ix_content_items_stage'), 'content_items', ['stage'], unique=False)
    op.create_index(op.f('ix_content_items_channel'), 'content_items', ['channel'], unique=False)
    op.create_index(op.f('ix_content_items_scheduled_at'), 'content_items', ['scheduled_at'], unique=False)
    op.create_index(op.f('ix_content_items_created_by'), 'content_items', ['created_by'], unique=False)

    # 2. portfolio_projects (Phase 13 Public Portfolio)
    op.create_table(
        'portfolio_projects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('tagline', sa.String(length=500), server_default='', nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('architecture_overview', sa.Text(), server_default='', nullable=False),
        sa.Column('challenges_solutions', sa.JSON(), nullable=True),
        sa.Column('tech_stack', sa.JSON(), nullable=False),
        sa.Column('category', sa.String(length=50), server_default='ai_agent', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='in_progress', nullable=False),
        sa.Column('github_url', sa.String(length=500), nullable=True),
        sa.Column('demo_url', sa.String(length=500), nullable=True),
        sa.Column('case_study_id', sa.UUID(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('is_public', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['case_study_id'], ['content_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_portfolio_projects_slug'), 'portfolio_projects', ['slug'], unique=True)
    op.create_index(op.f('ix_portfolio_projects_category'), 'portfolio_projects', ['category'], unique=False)
    op.create_index(op.f('ix_portfolio_projects_status'), 'portfolio_projects', ['status'], unique=False)
    op.create_index(op.f('ix_portfolio_projects_is_featured'), 'portfolio_projects', ['is_featured'], unique=False)
    op.create_index(op.f('ix_portfolio_projects_is_public'), 'portfolio_projects', ['is_public'], unique=False)

    # 3. contact_inquiries (Phase 13 Contact Form)
    op.create_table(
        'contact_inquiries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('source_ip', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # 4. eval_benchmark_runs (Phase 13 Eval Matrix Agent)
    op.create_table(
        'eval_benchmark_runs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('benchmark_type', sa.String(length=64), nullable=False),
        sa.Column('total_tests', sa.Integer(), nullable=False),
        sa.Column('passed', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=False),
        sa.Column('run_by', sa.UUID(), nullable=True),
        sa.Column('run_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['run_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_eval_benchmark_runs_benchmark_type'), 'eval_benchmark_runs', ['benchmark_type'], unique=False)


def downgrade() -> None:
    op.drop_table('eval_benchmark_runs')
    op.drop_table('contact_inquiries')
    op.drop_table('portfolio_projects')
    op.drop_table('content_items')
