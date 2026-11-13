"""phases_07_to_11_tables

Revision ID: 003_phases_07_to_11_tables
Revises: 002_agent_executions
Create Date: 2026-11-12 23:45:00.000000

"""
from typing import Sequence, Union
from alembic import context, op
import sqlalchemy as sa
from backend.app.models.vector_type import VectorType

revision: str = '003_phases_07_to_11_tables'
down_revision: Union[str, None] = '002_agent_executions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect_name = context.get_context().dialect.name
    if dialect_name == 'postgresql':
        op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # 1. llm_usage (Phase 07 AI Gateway)
    op.create_table(
        'llm_usage',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('agent_slug', sa.String(length=50), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('input_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('output_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_tokens', sa.Integer(), server_default='0', nullable=False),
        sa.Column('cost_usd', sa.Float(), server_default='0', nullable=False),
        sa.Column('latency_ms', sa.Integer(), server_default='0', nullable=False),
        sa.Column('task_type', sa.String(length=50), server_default='completion', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_llm_usage_id'), 'llm_usage', ['id'], unique=False)
    op.create_index(op.f('ix_llm_usage_user_id'), 'llm_usage', ['user_id'], unique=False)
    op.create_index(op.f('ix_llm_usage_agent_slug'), 'llm_usage', ['agent_slug'], unique=False)
    op.create_index(op.f('ix_llm_usage_provider'), 'llm_usage', ['provider'], unique=False)
    op.create_index(op.f('ix_llm_usage_model'), 'llm_usage', ['model'], unique=False)
    op.create_index(op.f('ix_llm_usage_created_at'), 'llm_usage', ['created_at'], unique=False)

    # 2. tool_approvals (Phase 08 MCP)
    op.create_table(
        'tool_approvals',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('agent_slug', sa.String(length=100), nullable=True),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('preview', sa.JSON(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), server_default='medium', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.UUID(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tool_approvals_user_id'), 'tool_approvals', ['user_id'], unique=False)
    op.create_index(op.f('ix_tool_approvals_agent_slug'), 'tool_approvals', ['agent_slug'], unique=False)
    op.create_index(op.f('ix_tool_approvals_tool_name'), 'tool_approvals', ['tool_name'], unique=False)
    op.create_index(op.f('ix_tool_approvals_status'), 'tool_approvals', ['status'], unique=False)

    # 3. tool_audits (Phase 08 MCP Immutable Audit Log)
    op.create_table(
        'tool_audits',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('agent_slug', sa.String(length=100), nullable=True),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('output_summary', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tool_audits_user_id'), 'tool_audits', ['user_id'], unique=False)
    op.create_index(op.f('ix_tool_audits_agent_slug'), 'tool_audits', ['agent_slug'], unique=False)
    op.create_index(op.f('ix_tool_audits_tool_name'), 'tool_audits', ['tool_name'], unique=False)
    op.create_index(op.f('ix_tool_audits_created_at'), 'tool_audits', ['created_at'], unique=False)

    # 4. knowledge_documents (Phase 10 RAG)
    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('source', sa.String(length=1024), nullable=False),
        sa.Column('doc_type', sa.String(length=50), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('total_chunks', sa.Integer(), server_default='0', nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('access_level', sa.String(length=50), server_default='private', nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_knowledge_documents_title'), 'knowledge_documents', ['title'], unique=False)
    op.create_index(op.f('ix_knowledge_documents_doc_type'), 'knowledge_documents', ['doc_type'], unique=False)
    op.create_index(op.f('ix_knowledge_documents_content_hash'), 'knowledge_documents', ['content_hash'], unique=False)
    op.create_index(op.f('ix_knowledge_documents_owner_id'), 'knowledge_documents', ['owner_id'], unique=False)
    op.create_index(op.f('ix_knowledge_documents_access_level'), 'knowledge_documents', ['access_level'], unique=False)
    op.create_index(op.f('ix_knowledge_documents_project_id'), 'knowledge_documents', ['project_id'], unique=False)
    op.create_index(op.f('ix_knowledge_documents_is_deleted'), 'knowledge_documents', ['is_deleted'], unique=False)

    # 5. document_chunks (Phase 10 RAG Vector Chunks)
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', VectorType(dim=768), nullable=True),
        sa.Column('token_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['knowledge_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_chunk_index'), 'document_chunks', ['chunk_index'], unique=False)

    # 6. knowledge_queries (Phase 10 RAG Query Telemetry)
    op.create_table(
        'knowledge_queries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('retrieved_chunks', sa.Integer(), server_default='0', nullable=False),
        sa.Column('top_score', sa.Float(), server_default='0', nullable=False),
        sa.Column('agent_slug', sa.String(length=100), nullable=True),
        sa.Column('response_used', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('duration_ms', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_knowledge_queries_user_id'), 'knowledge_queries', ['user_id'], unique=False)
    op.create_index(op.f('ix_knowledge_queries_agent_slug'), 'knowledge_queries', ['agent_slug'], unique=False)

    # 7. deployments (Phase 11 DevOps)
    op.create_table(
        'deployments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('environment', sa.String(length=50), server_default='staging', nullable=False),
        sa.Column('version', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('triggered_by', sa.UUID(), nullable=True),
        sa.Column('approved_by', sa.UUID(), nullable=True),
        sa.Column('checklist_result', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('rollback_of', sa.UUID(), nullable=True),
        sa.Column('notes', sa.Text(), server_default='', nullable=False),
        sa.ForeignKeyConstraint(['triggered_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['rollback_of'], ['deployments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_deployments_environment'), 'deployments', ['environment'], unique=False)
    op.create_index(op.f('ix_deployments_version'), 'deployments', ['version'], unique=False)
    op.create_index(op.f('ix_deployments_status'), 'deployments', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('deployments')
    op.drop_table('knowledge_queries')
    op.drop_table('document_chunks')
    op.drop_table('knowledge_documents')
    op.drop_table('tool_audits')
    op.drop_table('tool_approvals')
    op.drop_table('llm_usage')
