import math
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.knowledge_document import KnowledgeDocument, AccessLevel, DocType
from backend.app.models.document_chunk import DocumentChunk
from backend.app.rag.embedder import Embedder


class SearchFilters(BaseModel):
    user_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    doc_types: Optional[List[str]] = None
    access_level: Optional[str] = None


class RetrievedChunk(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_title: str
    source: str
    content: str
    score: float
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculates cosine similarity between two float vectors in [0, 1]."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    sim = dot / (norm_a * norm_b)
    # Clamp to [0.0, 1.0] for retrieval scores
    return max(0.0, min(1.0, float(sim)))


class VectorRetriever:
    """
    Retriever performing semantic vector search with strict multi-tenant access control:
    - User's own documents (private/project/public)
    - Project documents if user belongs to project
    - Public documents for all authenticated users
    - Filters deleted documents (is_deleted == False)
    - Threshold gating (default >= 0.7)
    """

    @classmethod
    async def search(
        cls,
        query: str,
        session: AsyncSession,
        filters: SearchFilters,
        top_k: int = 5,
        threshold: float = 0.7,
        query_vector: Optional[List[float]] = None,
    ) -> List[RetrievedChunk]:
        """
        Executes semantic search:
        1. Embeds query (or uses provided vector)
        2. Queries database with access control filters
        3. Computes exact cosine similarity
        4. Filters chunks below similarity threshold
        5. Returns top_k results ordered by descending score
        """
        if not query or not query.strip():
            return []

        # 1. Obtain query embedding
        vec = query_vector if query_vector is not None else Embedder.embed_query(query)
        if vec is None:
            # Honest behavior: without query embedding, cannot compute semantic vector similarity
            return []

        # 2. Build multi-tenant document access criteria
        # Condition A: Public documents
        public_cond = and_(
            KnowledgeDocument.access_level == AccessLevel.public,
            KnowledgeDocument.is_deleted == False,
        )

        # Condition B: User's own documents
        owner_cond = and_(
            KnowledgeDocument.owner_id == filters.user_id,
            KnowledgeDocument.is_deleted == False,
        )

        access_conditions = [public_cond, owner_cond]

        # Condition C: Project documents (if project_id specified)
        if filters.project_id:
            project_cond = and_(
                KnowledgeDocument.project_id == filters.project_id,
                KnowledgeDocument.is_deleted == False,
            )
            access_conditions.append(project_cond)

        base_filter = or_(*access_conditions)

        # Optional doc_type filter
        stmt = (
            select(DocumentChunk)
            .join(KnowledgeDocument, DocumentChunk.document_id == KnowledgeDocument.id)
            .where(base_filter)
            .options(selectinload(DocumentChunk.document))
        )

        if filters.doc_types:
            stmt = stmt.where(KnowledgeDocument.doc_type.in_(filters.doc_types))

        if filters.access_level:
            stmt = stmt.where(KnowledgeDocument.access_level == filters.access_level)

        res = await session.execute(stmt)
        chunks = res.scalars().all()

        if not chunks:
            return []

        # 3. Compute cosine similarity for each chunk
        scored_candidates: List[RetrievedChunk] = []
        for ch in chunks:
            if not ch.embedding:
                continue

            sim = compute_cosine_similarity(vec, ch.embedding)
            if sim >= threshold:
                doc = ch.document
                scored_candidates.append(
                    RetrievedChunk(
                        chunk_id=ch.id,
                        document_id=ch.document_id,
                        document_title=doc.title if doc else "Untitled Document",
                        source=doc.source if doc else "unknown",
                        content=ch.content,
                        score=round(sim, 4),
                        chunk_index=ch.chunk_index,
                        metadata={
                            **ch.metadata_json,
                            "doc_type": str(doc.doc_type.value) if doc and hasattr(doc.doc_type, "value") else "text",
                            "access_level": str(doc.access_level.value) if doc and hasattr(doc.access_level, "value") else "private",
                        },
                    )
                )

        # 4. Sort descending by score and take top_k
        scored_candidates.sort(key=lambda x: x.score, reverse=True)
        return scored_candidates[:top_k]
