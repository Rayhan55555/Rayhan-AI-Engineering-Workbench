import hashlib
import io
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.knowledge_document import KnowledgeDocument, DocType, AccessLevel
from backend.app.models.document_chunk import DocumentChunk
from backend.app.rag.chunker import TextChunker, ChunkStrategy
from backend.app.rag.embedder import Embedder

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

SUPPORTED_EXTENSIONS = {
    ".pdf": DocType.pdf,
    ".md": DocType.markdown,
    ".markdown": DocType.markdown,
    ".txt": DocType.text,
    ".py": DocType.code,
    ".ts": DocType.code,
    ".tsx": DocType.code,
    ".js": DocType.code,
    ".jsx": DocType.code,
    ".json": DocType.text,
    ".yaml": DocType.text,
    ".yml": DocType.text,
}

BLOCKED_EXTENSIONS = {
    ".env",
    ".zip",
    ".tar",
    ".gz",
    ".exe",
    ".bin",
    ".dll",
    ".so",
    ".pyc",
}


class IngestionResult(BaseModel):
    document_id: Optional[uuid.UUID] = None
    title: str
    source: str
    doc_type: str
    chunks_created: int = 0
    tokens_embedded: int = 0
    duration_ms: int = 0
    skipped: bool = False
    message: str = ""


class DocumentIngestionPipeline:
    """
    Ingestion pipeline:
    1. Validation: file type, size <= 10MB, blocked files (.env, archives)
    2. Extraction: pypdf text extraction, UTF-8 text decode
    3. Deduplication: SHA256 content hash check
    4. Strategy selection: CODE_AWARE, SEMANTIC, or FIXED_SIZE
    5. Chunking via TextChunker
    6. Embedding generation via Embedder
    7. Storage: KnowledgeDocument + DocumentChunk records
    """

    @classmethod
    def validate_and_detect_type(cls, filename: str, file_size: int) -> DocType:
        name_lower = filename.lower()

        # Check blocked files
        if name_lower == ".env" or name_lower.endswith(".env") or ".env." in name_lower:
            raise ValueError("Security violation: Ingestion of .env files is strictly forbidden.")

        ext = os.path.splitext(name_lower)[1]
        if ext in BLOCKED_EXTENSIONS:
            raise ValueError(f"Blocked file type '{ext}': Binaries and archive files cannot be ingested.")

        if file_size > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size ({file_size / (1024*1024):.1f}MB) exceeds the 10MB limit.")

        if ext in SUPPORTED_EXTENSIONS:
            return SUPPORTED_EXTENSIONS[ext]

        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS.keys())}"
        )

    @classmethod
    def extract_text(cls, content_bytes: bytes, filename: str) -> str:
        name_lower = filename.lower()
        if name_lower.endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content_bytes))
                page_texts = []
                for p_idx, page in enumerate(reader.pages):
                    pt = page.extract_text()
                    if pt:
                        page_texts.append(f"--- Page {p_idx + 1} ---\n{pt}")
                extracted = "\n\n".join(page_texts).strip()
                if not extracted:
                    raise ValueError("PDF contains no extractable text or is password-protected.")
                return extracted
            except Exception as e:
                raise ValueError(f"Failed to extract text from PDF: {str(e)}")
        else:
            try:
                return content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                # Try latin-1 fallback
                return content_bytes.decode("latin-1")

    @classmethod
    async def ingest_document(
        cls,
        session: AsyncSession,
        owner_id: uuid.UUID,
        title: str,
        content_bytes: Optional[bytes] = None,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        access_level: str = "private",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IngestionResult:
        start_time = time.monotonic()
        meta = metadata or {}

        # 1. Resolve content and source
        filename = ""
        raw_bytes = b""
        source = ""

        if content_bytes is not None and len(content_bytes) > 0:
            raw_bytes = content_bytes
            filename = meta.get("filename", title)
            source = meta.get("filename", "upload")
        elif file_path:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File '{file_path}' does not exist.")
            filename = os.path.basename(file_path)
            source = file_path
            with open(file_path, "rb") as f:
                raw_bytes = f.read()
        elif url:
            # URL ingestion
            source = url
            filename = url.split("/")[-1] or "web_document.txt"
            # Simulated fetch or mock text fetch for URL
            raw_text = f"# Knowledge URL: {url}\n\nIngested reference content for {url}."
            raw_bytes = raw_text.encode("utf-8")
        else:
            raise ValueError("No file content, file path, or URL provided for ingestion.")

        # 2. Validation
        doc_type = cls.validate_and_detect_type(filename, len(raw_bytes))

        # 3. Extraction
        text = cls.extract_text(raw_bytes, filename)
        if not text or not text.strip():
            raise ValueError("Extracted document content is empty.")

        # 4. Deduplication via SHA256
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        # Check existing documents for this owner/project
        existing_stmt = select(KnowledgeDocument).where(
            and_(
                KnowledgeDocument.content_hash == content_hash,
                KnowledgeDocument.is_deleted == False,
                KnowledgeDocument.owner_id == owner_id,
            )
        )
        res = await session.execute(existing_stmt)
        existing_doc = res.scalars().first()

        duration_ms = int((time.monotonic() - start_time) * 1000)

        if existing_doc:
            return IngestionResult(
                document_id=existing_doc.id,
                title=existing_doc.title,
                source=existing_doc.source,
                doc_type=existing_doc.doc_type.value,
                chunks_created=existing_doc.total_chunks,
                tokens_embedded=0,
                duration_ms=duration_ms,
                skipped=True,
                message=f"Duplicate document detected (SHA256: {content_hash[:8]}...). Skipped re-ingestion.",
            )

        # 5. Chunking
        if doc_type == DocType.code:
            strategy = ChunkStrategy.CODE_AWARE
        elif doc_type == DocType.markdown:
            strategy = ChunkStrategy.SEMANTIC
        elif doc_type == DocType.pdf:
            strategy = ChunkStrategy.SEMANTIC
        else:
            strategy = ChunkStrategy.FIXED_SIZE

        chunks = TextChunker.chunk(
            text=text,
            strategy=strategy,
            doc_type=doc_type.value,
            metadata={"filename": filename, "source": source},
        )

        if not chunks:
            raise ValueError("Document chunking produced zero chunks.")

        # 6. Embeddings (Batching)
        embedded_chunks = Embedder.embed_chunks(chunks)

        # 7. Persist KnowledgeDocument
        doc_access = AccessLevel(access_level) if access_level in [a.value for a in AccessLevel] else AccessLevel.private

        doc = KnowledgeDocument(
            title=title or filename or "Untitled Document",
            source=source,
            doc_type=doc_type,
            content_hash=content_hash,
            total_chunks=len(embedded_chunks),
            owner_id=owner_id,
            access_level=doc_access,
            project_id=project_id,
            metadata_json={
                **meta,
                "filename": filename,
                "file_size_bytes": len(raw_bytes),
                "strategy": strategy.value,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        session.add(doc)
        await session.flush()  # Obtain doc.id

        # Persist DocumentChunks
        total_tokens = 0
        for ec in embedded_chunks:
            total_tokens += ec.token_count
            chunk_row = DocumentChunk(
                document_id=doc.id,
                chunk_index=ec.metadata.get("chunk_index", 0),
                content=ec.content,
                embedding=ec.embedding,
                token_count=ec.token_count,
                metadata_json=ec.metadata,
            )
            session.add(chunk_row)

        await session.commit()
        await session.refresh(doc)

        duration_ms = int((time.monotonic() - start_time) * 1000)

        return IngestionResult(
            document_id=doc.id,
            title=doc.title,
            source=doc.source,
            doc_type=doc.doc_type.value,
            chunks_created=len(embedded_chunks),
            tokens_embedded=total_tokens,
            duration_ms=duration_ms,
            skipped=False,
            message=f"Successfully ingested '{doc.title}': {len(embedded_chunks)} chunks created and indexed.",
        )
