import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.models.knowledge_document import KnowledgeDocument
from backend.app.rag.ingestion import DocumentIngestionPipeline


@pytest.mark.asyncio
async def test_ingest_markdown_creates_chunks(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="pipeline_test@example.com",
        username="pipeline_user",
        hashed_password="pw",
    )
    db_session.add(user)
    await db_session.commit()

    content = (
        "# System Architecture Specification\n\n"
        "## Clean Architecture Layers\n"
        "The system strictly separates routers, services, models, and tools.\n\n"
        "## Data Access Layer\n"
        "PostgreSQL 15+ is used with pgvector for vector cosine distance calculations.\n"
    ).encode("utf-8")

    res = await DocumentIngestionPipeline.ingest_document(
        session=db_session,
        owner_id=user.id,
        title="Architecture Spec",
        content_bytes=content,
        access_level="private",
        metadata={"filename": "architecture.md"},
    )

    assert res.document_id is not None
    assert res.chunks_created >= 2
    assert res.skipped is False
    assert "Successfully ingested" in res.message


@pytest.mark.asyncio
async def test_duplicate_document_detection_skips_reingestion(db_session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="dedup_test@example.com",
        username="dedup_user",
        hashed_password="pw",
    )
    db_session.add(user)
    await db_session.commit()

    content = b"Identical technical specification document content for SHA256 test."

    # First ingestion
    res1 = await DocumentIngestionPipeline.ingest_document(
        session=db_session,
        owner_id=user.id,
        title="Spec Doc",
        content_bytes=content,
        metadata={"filename": "spec.txt"},
    )
    assert res1.skipped is False

    # Second ingestion with identical content
    res2 = await DocumentIngestionPipeline.ingest_document(
        session=db_session,
        owner_id=user.id,
        title="Spec Doc Duplicate",
        content_bytes=content,
        metadata={"filename": "spec.txt"},
    )
    assert res2.skipped is True
    assert "Duplicate document detected" in res2.message
    assert res2.document_id == res1.document_id


@pytest.mark.asyncio
async def test_ingestion_blocks_env_file(db_session: AsyncSession):
    user_id = uuid.uuid4()
    with pytest.raises(ValueError, match="Security violation.*\\.env"):
        await DocumentIngestionPipeline.ingest_document(
            session=db_session,
            owner_id=user_id,
            title="Secret Environment",
            content_bytes=b"SECRET_KEY=supersecret123\nAPI_KEY=xyz",
            metadata={"filename": ".env"},
        )


@pytest.mark.asyncio
async def test_ingestion_blocks_oversized_file(db_session: AsyncSession):
    user_id = uuid.uuid4()
    # 11MB dummy content
    large_bytes = b"0" * (11 * 1024 * 1024)
    with pytest.raises(ValueError, match="exceeds the 10MB limit"):
        await DocumentIngestionPipeline.ingest_document(
            session=db_session,
            owner_id=user_id,
            title="Large File",
            content_bytes=large_bytes,
            metadata={"filename": "large.txt"},
        )


@pytest.mark.asyncio
async def test_ingestion_blocks_binary_archive(db_session: AsyncSession):
    user_id = uuid.uuid4()
    with pytest.raises(ValueError, match="Blocked file type.*archive"):
        await DocumentIngestionPipeline.ingest_document(
            session=db_session,
            owner_id=user_id,
            title="Archive",
            content_bytes=b"PK\x03\x04fakezip",
            metadata={"filename": "bundle.zip"},
        )
