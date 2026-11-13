from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    document: str
    source: str
    chunk: str
    score: float
    page: Optional[int] = None
    line: Optional[int] = None
    chunk_index: Optional[int] = None
    strategy: Optional[str] = None


class CitationTracker:
    """
    Tracks and formats document citations to ensure zero fabricated references
    and rigorous ground-truth traceability.
    """

    @classmethod
    def format_citation(
        cls,
        document_title: str,
        source: str,
        content: str,
        score: float,
        metadata: Optional[Dict[str, Any]] = None,
        max_excerpt_len: int = 240,
    ) -> Citation:
        meta = metadata or {}
        # Clean excerpt
        clean_excerpt = content.strip().replace("\n", " ")
        if len(clean_excerpt) > max_excerpt_len:
            clean_excerpt = clean_excerpt[:max_excerpt_len].rstrip() + "..."

        page = meta.get("page")
        line = meta.get("start_line") or meta.get("line")
        chunk_idx = meta.get("chunk_index")
        strategy = meta.get("strategy")

        return Citation(
            document=document_title or "Untitled Document",
            source=source or "knowledge_base",
            chunk=clean_excerpt,
            score=round(float(score), 4),
            page=int(page) if page is not None else None,
            line=int(line) if line is not None else None,
            chunk_index=int(chunk_idx) if chunk_idx is not None else None,
            strategy=strategy,
        )

    @classmethod
    def from_retrieved_chunks(cls, chunks: List[Any]) -> List[Citation]:
        citations = []
        for ch in chunks:
            citations.append(
                cls.format_citation(
                    document_title=getattr(ch, "document_title", "Untitled Document"),
                    source=getattr(ch, "source", "unknown"),
                    content=getattr(ch, "content", ""),
                    score=getattr(ch, "score", 0.0),
                    metadata=getattr(ch, "metadata", {}),
                )
            )
        return citations
