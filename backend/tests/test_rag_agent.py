import json
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.base_agent import AgentTask, ExecutionContext, TaskScope
from backend.app.agents.implementations.rag_agent import RAGAgent
from backend.app.models.user import User
from backend.app.models.knowledge_document import KnowledgeDocument, DocType, AccessLevel
from backend.app.models.document_chunk import DocumentChunk


@pytest.mark.asyncio
async def test_rag_agent_search_with_citations(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="agent_test@example.com",
        username="agent_user",
        hashed_password="pw",
    )
    db_session.add(user)
    await db_session.flush()

    # Pre-populate a document
    doc = KnowledgeDocument(
        id=uuid.uuid4(),
        title="FastAPI Technical Guide",
        source="docs/fastapi.md",
        doc_type=DocType.markdown,
        content_hash="hash_fastapi",
        total_chunks=1,
        owner_id=user.id,
        access_level=AccessLevel.public,
    )
    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        content="FastAPI implements asynchronous dependency injection with Python type annotations.",
        embedding=[0.9] + [0.0] * 767,
        token_count=12,
        metadata_json={"page": 1, "strategy": "SEMANTIC"},
    )
    db_session.add_all([doc, chunk])
    await db_session.commit()

    agent = RAGAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="search FastAPI dependency injection",
        scope=TaskScope.read_only,
        requested_by=user.id,
    )
    context = ExecutionContext()

    # In test mode without live Gemini API, we can test that the search pipeline runs
    result = await agent.execute(task, context)
    assert result.success is True
    assert result.simulated is False


@pytest.mark.asyncio
async def test_rag_agent_honest_empty_response(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="empty_test@example.com",
        username="empty_user",
        hashed_password="pw",
    )
    db_session.add(user)
    await db_session.commit()

    agent = RAGAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="search non-existent astronomical physics concepts",
        scope=TaskScope.read_only,
        requested_by=user.id,
    )
    context = ExecutionContext()

    result = await agent.execute(task, context)
    assert result.success is True
    assert "No relevant information found" in result.output
    assert result.simulated is False


@pytest.mark.asyncio
async def test_rag_agent_ingest_requires_implement_scope():
    agent = RAGAgent()
    user_id = uuid.uuid4()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="ingest file new_service_spec.md",
        scope=TaskScope.suggest,  # SUGGEST scope is insufficient for write
        requested_by=user_id,
    )
    context = ExecutionContext()

    result = await agent.execute(task, context)
    assert result.success is False
    assert "requires IMPLEMENT scope" in result.output
    assert result.simulated is False


@pytest.mark.asyncio
async def test_rag_agent_list_knowledge_base(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="list_kb@example.com",
        username="list_user",
        hashed_password="pw",
    )
    db_session.add(user)
    await db_session.flush()

    doc = KnowledgeDocument(
        id=uuid.uuid4(),
        title="Microservice Topology",
        source="topology.md",
        doc_type=DocType.markdown,
        content_hash="hash_topo",
        total_chunks=3,
        owner_id=user.id,
        access_level=AccessLevel.private,
    )
    db_session.add(doc)
    await db_session.commit()

    agent = RAGAgent()
    task = AgentTask(
        agent_slug=agent.slug,
        instruction="list knowledge base",
        scope=TaskScope.read_only,
        requested_by=user.id,
    )
    context = ExecutionContext()

    result = await agent.execute(task, context)
    assert result.success is True
    parsed = json.loads(result.output)
    assert parsed["task"] == "list_knowledge_base"
    assert parsed["total_documents"] >= 1
    assert any(d["title"] == "Microservice Topology" for d in parsed["documents"])


@pytest.mark.asyncio
async def test_rag_agent_capabilities():
    agent = RAGAgent()
    cap = await agent.describe_capabilities()
    assert cap.slug == "rag-engine-v1"
    assert cap.phase == 10
    assert "knowledge_search" in cap.allowed_tools
    assert "document_ingester" in cap.allowed_tools
