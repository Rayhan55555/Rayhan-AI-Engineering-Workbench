import pytest
from backend.app.rag.chunker import TextChunker, ChunkStrategy, estimate_token_count


def test_fixed_size_chunking():
    text = " ".join([f"token_{i}" for i in range(1000)])
    chunks = TextChunker.chunk_fixed_size(text, chunk_size=200, overlap=30)

    assert len(chunks) > 1
    for ch in chunks:
        assert ch.strategy == ChunkStrategy.FIXED_SIZE.value
        assert ch.token_count > 0
        assert "chunk_index" in ch.metadata
    assert chunks[0].metadata["chunk_index"] == 0
    assert chunks[1].metadata["chunk_index"] == 1


def test_code_aware_chunking_python():
    code = (
        "import os\n"
        "from typing import List\n\n"
        "def compute_hash(val: str) -> str:\n"
        "    return val[::-1]\n\n"
        "class ModelContainer:\n"
        "    def __init__(self):\n"
        "        self.models = []\n\n"
        "    def add_model(self, model):\n"
        "        self.models.append(model)\n"
    )
    chunks = TextChunker.chunk_code_aware(code, language="python")

    assert len(chunks) >= 2
    # First chunk must contain imports
    assert "import os" in chunks[0].content
    assert chunks[0].strategy == ChunkStrategy.CODE_AWARE.value
    assert any("compute_hash" in ch.content for ch in chunks)
    assert any("ModelContainer" in ch.content for ch in chunks)


def test_semantic_chunking_markdown():
    markdown = (
        "# System Architecture\n"
        "The system uses FastAPI with PostgreSQL and pgvector for high-performance retrieval.\n\n"
        "## Vector Database\n"
        "pgvector allows vector cosine distance search with indexed IVFFLAT.\n\n"
        "## Ingestion Pipeline\n"
        "Documents are parsed, chunked, and embedded via Google text-embedding-004.\n"
    )
    chunks = TextChunker.chunk_semantic(markdown, min_tokens=10, max_tokens=100)

    assert len(chunks) >= 2
    for ch in chunks:
        assert ch.strategy == ChunkStrategy.SEMANTIC.value
        assert "section" in ch.metadata


def test_sentence_chunking():
    text = (
        "FastAPI is a modern web framework. "
        "It provides high performance with asyncio. "
        "PostgreSQL stores relational entities reliably. "
        "Pgvector provides semantic vector indexes. "
        "Clean architecture ensures decoupling. "
        "MCP standardizes tool calling."
    )
    chunks = TextChunker.chunk_sentence(text, sentences_per_chunk=3)

    assert len(chunks) == 2
    assert chunks[0].metadata["sentence_count"] == 3
    assert chunks[1].metadata["sentence_count"] == 3


def test_empty_content_handling():
    assert TextChunker.chunk_fixed_size("") == []
    assert TextChunker.chunk_code_aware("   ") == []
    assert TextChunker.chunk_semantic("\n\n\n") == []
    assert TextChunker.chunk_sentence("") == []
    assert TextChunker.chunk("", strategy=ChunkStrategy.FIXED_SIZE) == []


def test_token_count_estimation():
    assert estimate_token_count("") == 0
    tokens = estimate_token_count("Hello world from Rayhan Workbench")
    assert tokens >= 5
