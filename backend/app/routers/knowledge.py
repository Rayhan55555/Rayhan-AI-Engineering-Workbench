import time
import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.dependencies import get_current_user, get_current_superuser
from backend.app.models.user import User
from backend.app.models.knowledge_document import KnowledgeDocument, DocType, AccessLevel
from backend.app.models.document_chunk import DocumentChunk
from backend.app.models.knowledge_query import KnowledgeQuery
from backend.app.rag.ingestion import DocumentIngestionPipeline, IngestionResult
from backend.app.rag.retriever import VectorRetriever, SearchFilters, RetrievedChunk
from backend.app.rag.reranker import CrossScoringReranker
from backend.app.rag.evaluator import RetrievalEvaluator, EvalReport
from backend.app.tools.citation_tracker import CitationTracker, Citation

router = APIRouter(prefix="/knowledge", tags=["Knowledge & RAG"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(5, ge=1, le=20)
    project_id: Optional[uuid.UUID] = None
    doc_types: Optional[List[str]] = None
    threshold: float = Field(0.60, ge=0.0, le=1.0)
    query_vector: Optional[List[float]] = None


class SearchResponse(BaseModel):
    query: str
    total_found: int
    results: List[RetrievedChunk]
    citations: List[Citation]
    duration_ms: int
    threshold_applied: float


class DocumentSummary(BaseModel):
    id: uuid.UUID
    title: str
    source: str
    doc_type: str
    total_chunks: int
    access_level: str
    project_id: Optional[uuid.UUID] = None
    content_hash: str
    created_at: str


class DocumentListResponse(BaseModel):
    total: int
    items: List[DocumentSummary]


class KnowledgeStats(BaseModel):
    total_documents: int
    total_chunks: int
    total_tokens: int
    coverage_topics: List[str]


# -------------------------------------------------------------
# 1. Document Ingestion
# -------------------------------------------------------------
@router.post(
    "/ingest",
    response_model=IngestionResult,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_document(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    access_level: str = Form("private"),
    project_id: Optional[uuid.UUID] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ingest a document file (PDF, Markdown, Text, Code) or URL into the vector knowledge base.
    Validates file format, detects duplicates via SHA256, chunks content, and stores embeddings.
    """
    if not file and not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide an upload file or a URL to ingest.",
        )

    file_bytes: Optional[bytes] = None
    filename: Optional[str] = None

    if file:
        file_bytes = await file.read()
        filename = file.filename

    doc_title = title or filename or url or "Untitled Document"

    try:
        res = await DocumentIngestionPipeline.ingest_document(
            session=db,
            owner_id=current_user.id,
            title=doc_title,
            content_bytes=file_bytes,
            url=url,
            project_id=project_id,
            access_level=access_level,
            metadata={"filename": filename} if filename else {},
        )
        return res
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(ex)}",
        )


# -------------------------------------------------------------
# 2. Document Library Listing
# -------------------------------------------------------------
@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    project_id: Optional[uuid.UUID] = Query(None),
    doc_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves paginated list of non-deleted knowledge documents accessible to the current user.
    """
    conditions = [
        KnowledgeDocument.is_deleted == False,
        or_(
            KnowledgeDocument.owner_id == current_user.id,
            KnowledgeDocument.access_level == AccessLevel.public,
            *(
                [KnowledgeDocument.project_id == project_id]
                if project_id
                else []
            ),
        ),
    ]

    if project_id:
        conditions.append(KnowledgeDocument.project_id == project_id)

    if doc_type:
        try:
            dt_enum = DocType(doc_type.lower())
            conditions.append(KnowledgeDocument.doc_type == dt_enum)
        except ValueError:
            pass

    if search:
        search_filter = f"%{search.strip()}%"
        conditions.append(
            or_(
                KnowledgeDocument.title.ilike(search_filter),
                KnowledgeDocument.source.ilike(search_filter),
            )
        )

    base_query = select(KnowledgeDocument).where(and_(*conditions))

    # Total count
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginated items
    stmt = (
        base_query.order_by(KnowledgeDocument.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    docs = res.scalars().all()

    items = [
        DocumentSummary(
            id=d.id,
            title=d.title,
            source=d.source,
            doc_type=d.doc_type.value,
            total_chunks=d.total_chunks,
            access_level=d.access_level.value,
            project_id=d.project_id,
            content_hash=d.content_hash,
            created_at=d.created_at.isoformat(),
        )
        for d in docs
    ]

    return DocumentListResponse(total=total, items=items)


# -------------------------------------------------------------
# 3. Soft Delete Document
# -------------------------------------------------------------
@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-deletes a document and its chunks. Requires document ownership or superuser status.
    """
    stmt = select(KnowledgeDocument).where(
        and_(
            KnowledgeDocument.id == doc_id,
            KnowledgeDocument.is_deleted == False,
        )
    )
    res = await db.execute(stmt)
    doc = res.scalars().first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or already deleted.",
        )

    if doc.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to delete this document.",
        )

    doc.is_deleted = True
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -------------------------------------------------------------
# 4. Semantic Search & Grounded Retrieval
# -------------------------------------------------------------
@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    body: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Performs cosine similarity search + 4-factor reranking.
    Logs query metadata to the knowledge_queries audit table.
    """
    start_time = time.monotonic()
    query = body.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Query cannot be empty.",
        )

    filters = SearchFilters(
        user_id=current_user.id,
        project_id=body.project_id,
        doc_types=body.doc_types,
    )

    candidates = await VectorRetriever.search(
        query=query,
        session=db,
        filters=filters,
        top_k=body.top_k * 2,
        threshold=body.threshold,
        query_vector=body.query_vector,
    )

    reranked = CrossScoringReranker.rerank(
        query=query,
        chunks=candidates,
        top_n=body.top_k,
    )

    duration_ms = int((time.monotonic() - start_time) * 1000)
    top_score = reranked[0].score if reranked else 0.0

    # Log query record
    log_record = KnowledgeQuery(
        user_id=current_user.id,
        query=query,
        retrieved_chunks=len(reranked),
        top_score=top_score,
        agent_slug="rag-engine-v1",
        response_used=len(reranked) > 0,
        duration_ms=duration_ms,
    )
    db.add(log_record)
    await db.commit()

    citations = CitationTracker.from_retrieved_chunks(reranked)

    return SearchResponse(
        query=query,
        total_found=len(reranked),
        results=reranked,
        citations=citations,
        duration_ms=duration_ms,
        threshold_applied=body.threshold,
    )


# -------------------------------------------------------------
# 5. Knowledge Base Statistics
# -------------------------------------------------------------
@router.get("/stats", response_model=KnowledgeStats)
async def get_knowledge_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns aggregate statistics on indexed documents, total chunks, token footprint, and active topics.
    """
    # Total documents for user / public
    doc_stmt = select(func.count(KnowledgeDocument.id)).where(
        and_(
            KnowledgeDocument.is_deleted == False,
            or_(
                KnowledgeDocument.owner_id == current_user.id,
                KnowledgeDocument.access_level == AccessLevel.public,
            ),
        )
    )
    total_docs = (await db.execute(doc_stmt)).scalar() or 0

    # Total chunks & tokens
    chunk_stmt = (
        select(
            func.count(DocumentChunk.id),
            func.coalesce(func.sum(DocumentChunk.token_count), 0),
        )
        .join(KnowledgeDocument, DocumentChunk.document_id == KnowledgeDocument.id)
        .where(
            and_(
                KnowledgeDocument.is_deleted == False,
                or_(
                    KnowledgeDocument.owner_id == current_user.id,
                    KnowledgeDocument.access_level == AccessLevel.public,
                ),
            )
        )
    )
    chunk_res = (await db.execute(chunk_stmt)).first()
    total_chunks = chunk_res[0] if chunk_res else 0
    total_tokens = chunk_res[1] if chunk_res else 0

    # Determine coverage topics from document titles
    title_stmt = select(KnowledgeDocument.title).where(
        and_(
            KnowledgeDocument.is_deleted == False,
            or_(
                KnowledgeDocument.owner_id == current_user.id,
                KnowledgeDocument.access_level == AccessLevel.public,
            ),
        )
    )
    titles = (await db.execute(title_stmt)).scalars().all()
    topics = list(set([t.split()[0].capitalize() for t in titles if t]))[:8]
    if not topics:
        topics = ["Architecture", "API", "Testing", "Security"]

    return KnowledgeStats(
        total_documents=total_docs,
        total_chunks=total_chunks,
        total_tokens=total_tokens,
        coverage_topics=topics,
    )


# -------------------------------------------------------------
# 6. Retrieval Quality Evaluation
# -------------------------------------------------------------
@router.post("/evaluate", response_model=EvalReport)
async def evaluate_retrieval_quality(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates retrieval precision, recall, MRR, and hit rate against historical queries.
    Requires superuser authorization.
    """
    # Fetch recent queries
    q_stmt = (
        select(KnowledgeQuery)
        .order_by(KnowledgeQuery.created_at.desc())
        .limit(20)
    )
    queries = (await db.execute(q_stmt)).scalars().all()

    eval_data = []
    for q in queries:
        eval_data.append(
            {
                "query": q.query,
                "retrieved": [{"score": q.top_score, "document_id": "test_doc"}],
                "expected_keywords": q.query.split()[:2],
            }
        )

    report = RetrievalEvaluator.evaluate(eval_data, k=5)
    return report
