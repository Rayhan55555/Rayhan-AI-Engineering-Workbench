import uuid
from typing import Any, Dict, Optional
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
import backend.app.database as db_module
from backend.app.rag.ingestion import DocumentIngestionPipeline
from backend.app.tools.base_tool import BaseTool, ToolResult


class DocumentIngesterTool(BaseTool):
    name = "document_ingester"
    description = "Ingests files or URLs into the vector knowledge base. Consequential write operation requiring IMPLEMENT scope and approval."
    required_permission = PermissionLevel.IMPLEMENT
    safe_by_default = False

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        title = params.get("title", "").strip()
        file_path = params.get("file_path")
        content_bytes = params.get("content_bytes")
        url = params.get("url")
        project_id = params.get("project_id")
        access_level = params.get("access_level", "private")
        metadata = params.get("metadata", {})

        if not file_path and not content_bytes and not url:
            return ToolResult(
                success=False,
                output="Must provide file_path, content_bytes, or url for document ingestion.",
                error="missing_content",
                simulated=False,
            )

        async with db_module.AsyncSessionLocal() as session:
            try:
                res = await DocumentIngestionPipeline.ingest_document(
                    session=session,
                    owner_id=context.user_id,
                    title=title or "Ingested Document",
                    content_bytes=content_bytes,
                    file_path=file_path,
                    url=url,
                    project_id=uuid.UUID(str(project_id)) if project_id else None,
                    access_level=access_level,
                    metadata=metadata,
                )
                return ToolResult(
                    success=True,
                    output=res.model_dump(),
                    metadata=res.model_dump(),
                    evidence=[
                        f"Ingested '{res.title}' with {res.chunks_created} chunks ({res.tokens_embedded} tokens)"
                    ],
                    simulated=False,
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    output=f"Document ingestion failed: {str(e)}",
                    error=str(e),
                    simulated=False,
                )
