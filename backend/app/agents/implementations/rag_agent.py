import json
import logging
import re
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from backend.app.agents.base_agent import (
    AgentResult,
    AgentTask,
    Artifact,
    BaseAgent,
    CapabilityDescription,
    Evidence,
    ExecutionContext,
    TaskScope,
    ValidationResult,
)
import backend.app.database as db_module
from backend.app.models.knowledge_document import KnowledgeDocument
from backend.app.rag.retriever import VectorRetriever, SearchFilters
from backend.app.rag.reranker import CrossScoringReranker
from backend.app.rag.ingestion import DocumentIngestionPipeline
from backend.app.tools.citation_tracker import CitationTracker, Citation

logger = logging.getLogger("agent.rag")


class RAGAgent(BaseAgent):
    """
    RAG / Knowledge Agent (rag-engine-v1).
    Full operational implementation (simulated=False).
    Provides semantic vector retrieval, cross-scoring reranking,
    citation-grounded answer synthesis, and document ingestion pipeline.
    """

    slug = "rag-engine-v1"
    name = "Knowledge Architect RAG Agent"
    purpose = "Semantic vector search, cross-scoring reranking, citation-grounded document synthesis, and access-controlled document ingestion."
    phase = 10
    version = "1.0.0"
    allowed_tools = ["knowledge_search", "document_ingester", "citation_tracker"]
    required_permissions = ["READ_ONLY", "SUGGEST", "IMPLEMENT"]
    limitations = [
        "Vector search constrained to indexed documents only",
        "Dense semantic retrieval requires text-embedding-004 embeddings",
        "Document ingestion requires explicit human approval under IMPLEMENT scope",
        "Never fabricates citation sources or answers without supporting evidence",
    ]

    async def validate_input(self, task: AgentTask) -> ValidationResult:
        instruction = task.instruction.strip()
        if len(instruction) < 3:
            return ValidationResult(
                valid=False,
                error="Instruction is too short (minimum 3 characters required).",
            )
        if len(instruction) > 4000:
            return ValidationResult(
                valid=False,
                error="Instruction exceeds maximum length of 4000 characters.",
            )
        return ValidationResult(valid=True)

    async def execute(self, task: AgentTask, context: ExecutionContext) -> AgentResult:
        val = await self.validate_input(task)
        if not val.valid:
            return AgentResult(
                success=False,
                output=f"Input validation rejected: {val.error}",
                limitations=self.limitations,
                simulated=False,
            )

        instruction = task.instruction.strip()
        instruction_lower = instruction.lower()
        artifacts: List[Artifact] = []
        evidence: List[Evidence] = []

        # -------------------------------------------------------------
        # 1. IMPLEMENT TASKS: Document Ingestion (Approval Required)
        # -------------------------------------------------------------
        if any(w in instruction_lower for w in ("ingest", "index file", "index url", "add document", "upload")):
            if task.scope != TaskScope.implement:
                return AgentResult(
                    success=False,
                    output="Document ingestion alters the knowledge base and requires IMPLEMENT scope with explicit human approval.",
                    limitations=self.limitations,
                    simulated=False,
                )

            # Extract target from instruction
            file_match = re.search(r"(?:ingest|index|add)\s+(?:file\s+)?([^\s]+\.[a-zA-Z0-9]+)", instruction, re.IGNORECASE)
            url_match = re.search(r"https?://[^\s]+", instruction)

            target_file = file_match.group(1) if file_match else None
            target_url = url_match.group(0) if url_match else None

            if not target_file and not target_url:
                # Check for bare words after ingest
                parts = instruction.split()
                if len(parts) >= 2:
                    target_file = parts[1]

            async with db_module.AsyncSessionLocal() as session:
                try:
                    res = await DocumentIngestionPipeline.ingest_document(
                        session=session,
                        owner_id=task.requested_by,
                        title=target_file or target_url or "Ingested Document",
                        file_path=target_file if target_file and not target_url else None,
                        url=target_url,
                        project_id=context.project_id,
                        access_level="private",
                    )

                    evidence.append(
                        Evidence(
                            source="ingestion_pipeline",
                            snippet=f"Ingested '{res.title}' ({res.chunks_created} chunks, {res.tokens_embedded} tokens)",
                            confidence=1.0,
                        )
                    )

                    report_output = {
                        "action": "document_ingestion",
                        "status": "skipped" if res.skipped else "success",
                        "document_id": str(res.document_id) if res.document_id else None,
                        "title": res.title,
                        "chunks_created": res.chunks_created,
                        "tokens_embedded": res.tokens_embedded,
                        "duration_ms": res.duration_ms,
                        "message": res.message,
                    }

                    return AgentResult(
                        success=True,
                        output=json.dumps(report_output, indent=2),
                        artifacts=artifacts,
                        evidence=evidence,
                        limitations=self.limitations,
                        simulated=False,
                    )
                except Exception as ex:
                    return AgentResult(
                        success=False,
                        output=f"Ingestion failed: {str(ex)}",
                        error=str(ex),
                        limitations=self.limitations,
                        simulated=False,
                    )

        # -------------------------------------------------------------
        # 2. READ_ONLY TASKS: List Knowledge Base
        # -------------------------------------------------------------
        if any(w in instruction_lower for w in ("list knowledge base", "list documents", "show knowledge base", "all documents")):
            async with db_module.AsyncSessionLocal() as session:
                stmt = (
                    select(KnowledgeDocument)
                    .where(
                        and_(
                            KnowledgeDocument.is_deleted == False,
                            KnowledgeDocument.owner_id == task.requested_by,
                        )
                    )
                    .order_by(KnowledgeDocument.created_at.desc())
                )
                res = await session.execute(stmt)
                docs = res.scalars().all()

                doc_list = [
                    {
                        "id": str(d.id),
                        "title": d.title,
                        "source": d.source,
                        "doc_type": d.doc_type.value,
                        "total_chunks": d.total_chunks,
                        "access_level": d.access_level.value,
                        "created_at": d.created_at.isoformat(),
                    }
                    for d in docs
                ]

                evidence.append(
                    Evidence(
                        source="knowledge_documents_db",
                        snippet=f"Enumerated {len(docs)} documents for user",
                        confidence=1.0,
                    )
                )

                output_dict = {
                    "task": "list_knowledge_base",
                    "total_documents": len(docs),
                    "documents": doc_list,
                }

                return AgentResult(
                    success=True,
                    output=json.dumps(output_dict, indent=2),
                    artifacts=artifacts,
                    evidence=evidence,
                    limitations=self.limitations,
                    simulated=False,
                )

        # -------------------------------------------------------------
        # 3. SUGGEST TASKS: Knowledge Gaps & Document Suggestions
        # -------------------------------------------------------------
        if any(w in instruction_lower for w in ("find gaps", "coverage gap", "missing topic")):
            async with db_module.AsyncSessionLocal() as session:
                stmt = select(KnowledgeDocument).where(
                    and_(
                        KnowledgeDocument.is_deleted == False,
                        KnowledgeDocument.owner_id == task.requested_by,
                    )
                )
                res = await session.execute(stmt)
                docs = res.scalars().all()

                titles = [d.title.lower() for d in docs]
                expected_topics = ["fastapi", "postgresql", "security", "testing", "architecture", "mcp", "rag", "deployment"]
                missing = [t for t in expected_topics if not any(t in title for title in titles)]

                gap_report = {
                    "task": "knowledge_gap_analysis",
                    "indexed_document_count": len(docs),
                    "identified_gaps": missing,
                    "recommendations": [
                        f"Consider ingesting documentation on: {topic.capitalize()}" for topic in missing
                    ],
                }

                return AgentResult(
                    success=True,
                    output=json.dumps(gap_report, indent=2),
                    artifacts=artifacts,
                    evidence=[Evidence(source="gap_analyzer", snippet=f"Identified {len(missing)} missing topics", confidence=0.9)],
                    limitations=self.limitations,
                    simulated=False,
                )

        # -------------------------------------------------------------
        # 4. DEFAULT: Semantic Retrieval & Citation-Grounded Answer
        # -------------------------------------------------------------
        # Clean search query from command prefixes
        search_query = re.sub(
            r"^(?:search|find documents? about|what do you know about|tell me about|retrieve|explain)\s+",
            "",
            instruction,
            flags=re.IGNORECASE,
        ).strip()
        if not search_query:
            search_query = instruction

        filters = SearchFilters(
            user_id=task.requested_by,
            project_id=context.project_id,
        )

        async with db_module.AsyncSessionLocal() as session:
            candidates = await VectorRetriever.search(
                query=search_query,
                session=session,
                filters=filters,
                top_k=6,
                threshold=0.60,
            )

            reranked = CrossScoringReranker.rerank(
                query=search_query,
                chunks=candidates,
                top_n=3,
            )

            # HONEST FALLBACK: Never fabricate an answer if no relevant chunks found
            if not reranked:
                honest_msg = f"No relevant information found in the knowledge base for: '{search_query}'."
                return AgentResult(
                    success=True,
                    output=honest_msg,
                    artifacts=[],
                    evidence=[
                        Evidence(
                            source="vector_retriever",
                            snippet="Zero chunks exceeded the 0.60 similarity threshold.",
                            confidence=1.0,
                        )
                    ],
                    limitations=self.limitations,
                    simulated=False,
                )

            # Format citations
            citations: List[Citation] = CitationTracker.from_retrieved_chunks(reranked)

            for c in citations:
                evidence.append(
                    Evidence(
                        source=f"Doc: {c.document} ({c.source})",
                        snippet=c.chunk,
                        confidence=c.score,
                    )
                )

            # Build grounded answer exclusively from retrieved excerpts
            excerpts = []
            for idx, c in enumerate(citations, 1):
                excerpts.append(f"[{idx}] {c.document} (Score: {c.score}):\n\"{c.chunk}\"")

            answer_body = (
                f"Based on {len(citations)} source documents retrieved from the knowledge base for '{search_query}':\n\n"
                + "\n\n".join(excerpts)
            )

            response_data = {
                "query": search_query,
                "answer": answer_body,
                "sources": [c.model_dump() for c in citations],
                "confidence": round(sum(c.score for c in citations) / len(citations), 4),
                "simulated": False,
            }

            artifacts.append(
                Artifact(
                    name="citations.json",
                    artifact_type="knowledge_citations",
                    content=json.dumps([c.model_dump() for c in citations], indent=2),
                    metadata={"query": search_query, "count": len(citations)},
                )
            )

            return AgentResult(
                success=True,
                output=json.dumps(response_data, indent=2),
                artifacts=artifacts,
                evidence=evidence,
                limitations=self.limitations,
                simulated=False,
            )

    async def describe_capabilities(self) -> CapabilityDescription:
        return CapabilityDescription(
            slug=self.slug,
            name=self.name,
            purpose=self.purpose,
            phase=self.phase,
            version=self.version,
            allowed_tools=self.allowed_tools,
            required_permissions=self.required_permissions,
            limitations=self.limitations,
        )
