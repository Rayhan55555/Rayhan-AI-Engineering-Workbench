import uuid
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
import backend.app.database as db_module
from backend.app.rag.retriever import VectorRetriever, SearchFilters
from backend.app.rag.reranker import CrossScoringReranker
from backend.app.tools.base_tool import BaseTool, ToolResult
from backend.app.tools.citation_tracker import CitationTracker


class KnowledgeSearchTool(BaseTool):
    name = "knowledge_search"
    description = "Searches knowledge base documents using dense vector cosine similarity and cross-scoring reranking."
    required_permission = PermissionLevel.READ_ONLY
    safe_by_default = True

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        query = params.get("query", "").strip()
        if not query:
            return ToolResult(
                success=False,
                output="Search query cannot be empty.",
                error="empty_query",
                simulated=False,
            )

        top_k = int(params.get("top_k", 5))
        threshold = float(params.get("threshold", 0.65))
        project_id = params.get("project_id")
        doc_types = params.get("doc_types")
        query_vector = params.get("query_vector")

        filters = SearchFilters(
            user_id=context.user_id,
            project_id=uuid.UUID(str(project_id)) if project_id else None,
            doc_types=doc_types if isinstance(doc_types, list) else None,
        )

        async with db_module.AsyncSessionLocal() as session:
            candidates = await VectorRetriever.search(
                query=query,
                session=session,
                filters=filters,
                top_k=top_k * 2,
                threshold=threshold,
                query_vector=query_vector,
            )

            reranked = CrossScoringReranker.rerank(
                query=query,
                chunks=candidates,
                top_n=top_k,
            )

            citations = CitationTracker.from_retrieved_chunks(reranked)

            return ToolResult(
                success=True,
                output=[c.model_dump() for c in reranked],
                metadata={
                    "query": query,
                    "retrieved_count": len(candidates),
                    "reranked_count": len(reranked),
                    "citations": [c.model_dump() for c in citations],
                },
                evidence=[
                    f"Retrieved {len(reranked)} chunks matching query '{query}' (threshold >= {threshold})"
                ],
                simulated=False,
            )
