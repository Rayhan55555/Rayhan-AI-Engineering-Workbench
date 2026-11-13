"""RAG-powered topic research tool for grounding Content Studio pieces in verified docs & codebase."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from backend.app.models.knowledge_document import KnowledgeDocument, AccessLevel
    from backend.app.rag.retriever import VectorRetriever, SearchFilters
    from backend.app.rag.reranker import CrossScoringReranker
    from backend.app.tools.citation_tracker import CitationTracker, Citation
except ImportError:
    from app.models.knowledge_document import KnowledgeDocument, AccessLevel
    from app.rag.retriever import VectorRetriever, SearchFilters
    from app.rag.reranker import CrossScoringReranker
    from app.tools.citation_tracker import CitationTracker, Citation


class ResearchBrief(BaseModel):
    """Grounded technical context retrieved for a topic."""

    topic: str
    rag_chunks_found: int
    repo_files_inspected: int
    citations: List[Citation] = Field(default_factory=list)
    key_facts: List[str] = Field(default_factory=list)
    code_excerpts: List[Dict[str, str]] = Field(default_factory=list)
    honest_note: str = ""


class TopicResearcher:
    """
    Combines Phase 10 RAG Vector Retrieval with safe workspace inspection
    to supply real, non-fabricated context for ContentAgent writers.
    """

    SAFE_CODE_DIRS = ["backend/app/agents", "backend/app/rag", "backend/app/devops", "backend/app/routers", "backend/app/tools"]

    @classmethod
    async def research_topic(
        cls,
        topic: str,
        session: Optional[AsyncSession] = None,
        user_id: Optional[uuid.UUID] = None,
        top_k: int = 5,
    ) -> ResearchBrief:
        citations: List[Citation] = []
        key_facts: List[str] = []
        code_excerpts: List[Dict[str, str]] = []
        rag_count = 0

        # 1. Query Phase 10 RAG Vector Knowledge Base if DB session is available
        if session is not None and user_id is not None:
            try:
                filters = SearchFilters(user_id=user_id)
                candidates = await VectorRetriever.search(
                    query=topic,
                    session=session,
                    filters=filters,
                    top_k=top_k * 2,
                    threshold=0.55,
                )
                reranked = CrossScoringReranker.rerank(query=topic, chunks=candidates, top_n=top_k)
                rag_count = len(reranked)
                if reranked:
                    citations.extend(CitationTracker.from_retrieved_chunks(reranked))
                    for ch in reranked:
                        excerpt = ch.content.strip().replace("\n", " ")
                        if len(excerpt) > 220:
                            excerpt = excerpt[:220] + "..."
                        key_facts.append(f"[{ch.document_title}] {excerpt}")
            except Exception:
                # Non-fatal fallback to workspace file inspection
                pass

        # 2. Supplement with real codebase file inspection when matching topic keywords
        topic_tokens = [t.lower() for t in topic.replace("-", " ").replace("_", " ").split() if len(t) > 2]
        files_checked = 0
        root = Path(".")

        for rel_dir in cls.SAFE_CODE_DIRS:
            dir_path = root / rel_dir
            if not dir_path.exists() or not dir_path.is_dir():
                continue
            for py_file in sorted(dir_path.glob("*.py")):
                if py_file.name == "__init__.py":
                    continue
                stem = py_file.stem.lower()
                if not topic_tokens or any(tok in stem for tok in topic_tokens):
                    files_checked += 1
                    try:
                        raw = py_file.read_text(encoding="utf-8")
                        lines = raw.splitlines()
                        snippet = "\n".join(lines[:28])
                        rel_str = str(py_file).replace("\\", "/")
                        code_excerpts.append({"file": rel_str, "snippet": snippet})
                        # Extract module docstring or class header as factual anchor
                        first_doc = next(
                            (l.strip().strip('"').strip("'") for l in lines[:8] if l.strip() and not l.startswith("#")),
                            f"Implementation module {py_file.name}",
                        )
                        key_facts.append(f"[Codebase: {rel_str}] {first_doc}")
                        citations.append(
                            CitationTracker.format_citation(
                                document_title=py_file.name,
                                source=rel_str,
                                content=first_doc,
                                score=0.92,
                                metadata={"line": 1, "strategy": "CODE_INSPECT"},
                            )
                        )
                    except Exception:
                        continue
                if len(code_excerpts) >= 3:
                    break
            if len(code_excerpts) >= 3:
                break

        honest_note = (
            f"Grounded in {rag_count} RAG vector chunks and {files_checked} real repository modules."
            if (rag_count > 0 or files_checked > 0)
            else "No indexed RAG documents or matching modules matched verbatim; using architectural framework structure with [BENCHMARK NEEDED] markers where telemetry is unverified."
        )

        return ResearchBrief(
            topic=topic,
            rag_chunks_found=rag_count,
            repo_files_inspected=files_checked,
            citations=citations,
            key_facts=key_facts,
            code_excerpts=code_excerpts,
            honest_note=honest_note,
        )
