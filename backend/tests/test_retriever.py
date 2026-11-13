import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.models.knowledge_document import KnowledgeDocument, DocType, AccessLevel
from backend.app.models.document_chunk import DocumentChunk
from backend.app.rag.retriever import VectorRetriever, SearchFilters, compute_cosine_similarity
from backend.app.rag.reranker import CrossScoringReranker


def test_compute_cosine_similarity_math():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert compute_cosine_similarity(v1, v2) == 1.0

    v3 = [0.0, 1.0, 0.0]
    assert compute_cosine_similarity(v1, v3) == 0.0

    v4 = [0.5, 0.5, 0.0]
    sim = compute_cosine_similarity(v1, v4)
    assert 0.70 < sim < 0.72


@pytest.mark.asyncio
async def test_retriever_access_control(db_session: AsyncSession):
    user_a = User(
        id=uuid.uuid4(),
        email="usera@example.com",
        username="usera",
        hashed_password="pw",
    )
    user_b = User(
        id=uuid.uuid4(),
        email="userb@example.com",
        username="userb",
        hashed_password="pw",
    )
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    # Document 1: User A's private doc
    doc_a = KnowledgeDocument(
        id=uuid.uuid4(),
        title="User A Private Spec",
        source="spec_a.md",
        doc_type=DocType.markdown,
        content_hash="hash_a",
        total_chunks=1,
        owner_id=user_a.id,
        access_level=AccessLevel.private,
    )
    chunk_a = DocumentChunk(
        document_id=doc_a.id,
        chunk_index=0,
        content="Secret proprietary architecture of User A",
        embedding=[1.0] + [0.0] * 767,
        token_count=10,
    )

    # Document 2: User B's private doc
    doc_b = KnowledgeDocument(
        id=uuid.uuid4(),
        title="User B Private Spec",
        source="spec_b.md",
        doc_type=DocType.markdown,
        content_hash="hash_b",
        total_chunks=1,
        owner_id=user_b.id,
        access_level=AccessLevel.private,
    )
    chunk_b = DocumentChunk(
        document_id=doc_b.id,
        chunk_index=0,
        content="Secret algorithm of User B",
        embedding=[1.0] + [0.0] * 767,
        token_count=10,
    )

    # Document 3: Public doc
    doc_pub = KnowledgeDocument(
        id=uuid.uuid4(),
        title="Public Handbook",
        source="handbook.md",
        doc_type=DocType.markdown,
        content_hash="hash_pub",
        total_chunks=1,
        owner_id=user_b.id,
        access_level=AccessLevel.public,
    )
    chunk_pub = DocumentChunk(
        document_id=doc_pub.id,
        chunk_index=0,
        content="Public engineering guide for everyone",
        embedding=[1.0] + [0.0] * 767,
        token_count=10,
    )

    db_session.add_all([doc_a, chunk_a, doc_b, chunk_b, doc_pub, chunk_pub])
    await db_session.commit()

    # Query vector identical to [1.0, 0.0, ...]
    q_vec = [1.0] + [0.0] * 767

    # User A searches -> should see doc_a (own) and doc_pub (public), but NOT doc_b (User B's private)
    filters_a = SearchFilters(user_id=user_a.id)
    results_a = await VectorRetriever.search(
        query="architecture",
        session=db_session,
        filters=filters_a,
        top_k=5,
        threshold=0.5,
        query_vector=q_vec,
    )

    doc_ids_a = [r.document_id for r in results_a]
    assert doc_a.id in doc_ids_a
    assert doc_pub.id in doc_ids_a
    assert doc_b.id not in doc_ids_a, "User A must not access User B's private documents"


@pytest.mark.asyncio
async def test_retriever_threshold_filters_low_matches(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="threshold@example.com",
        username="threshold_user",
        hashed_password="pw",
    )
    db_session.add(user)
    await db_session.flush()

    doc = KnowledgeDocument(
        id=uuid.uuid4(),
        title="Orthogonal Topics",
        source="orthogonal.txt",
        doc_type=DocType.text,
        content_hash="hash_orth",
        total_chunks=1,
        owner_id=user.id,
        access_level=AccessLevel.private,
    )
    # Vector orthogonal to query
    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        content="Completely unrelated topic",
        embedding=[0.0, 1.0] + [0.0] * 766,
        token_count=10,
    )
    db_session.add_all([doc, chunk])
    await db_session.commit()

    # Query vector is along dim 0
    q_vec = [1.0] + [0.0] * 767

    results = await VectorRetriever.search(
        query="machine learning",
        session=db_session,
        filters=SearchFilters(user_id=user.id),
        threshold=0.7,
        query_vector=q_vec,
    )

    assert len(results) == 0, "Low similarity matches must be filtered out by threshold"


@pytest.mark.asyncio
async def test_empty_knowledge_base_returns_empty(db_session: AsyncSession):
    random_user_id = uuid.uuid4()
    q_vec = [1.0] + [0.0] * 767

    results = await VectorRetriever.search(
        query="anything",
        session=db_session,
        filters=SearchFilters(user_id=random_user_id),
        threshold=0.6,
        query_vector=q_vec,
    )

    assert results == []


def test_cross_scoring_reranker_ordering():
    from backend.app.rag.retriever import RetrievedChunk
    chunk_1 = RetrievedChunk(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_title="FastAPI Guide",
        source="fastapi.md",
        content="FastAPI sliding window rate limiting implementation and authentication with JWT.",
        score=0.85,
        chunk_index=0,
    )
    chunk_2 = RetrievedChunk(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_title="Unrelated Document",
        source="other.md",
        content="General database information without relevant keywords.",
        score=0.80,
        chunk_index=1,
    )

    reranked = CrossScoringReranker.rerank(
        query="FastAPI rate limiting",
        chunks=[chunk_2, chunk_1],
        top_n=2,
    )

    assert len(reranked) == 2
    # chunk_1 has both higher similarity and query term overlap
    assert reranked[0].document_title == "FastAPI Guide"
    assert reranked[0].score > reranked[1].score
