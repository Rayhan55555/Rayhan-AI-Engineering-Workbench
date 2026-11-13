"""
RAG & Knowledge System for Rayhan AI Engineering Workbench.
Provides text chunking, embedding generation via Google text-embedding-004,
cosine similarity vector retrieval, cross-scoring reranking,
document ingestion pipeline, and retrieval quality evaluation.
"""

from backend.app.rag.chunker import TextChunker, ChunkStrategy, ChunkResult
from backend.app.rag.embedder import Embedder, EmbeddedChunk
from backend.app.rag.retriever import VectorRetriever, RetrievedChunk, SearchFilters
from backend.app.rag.reranker import CrossScoringReranker
from backend.app.rag.ingestion import DocumentIngestionPipeline, IngestionResult
from backend.app.rag.evaluator import RetrievalEvaluator, EvalReport

__all__ = [
    "TextChunker",
    "ChunkStrategy",
    "ChunkResult",
    "Embedder",
    "EmbeddedChunk",
    "VectorRetriever",
    "RetrievedChunk",
    "SearchFilters",
    "CrossScoringReranker",
    "DocumentIngestionPipeline",
    "IngestionResult",
    "RetrievalEvaluator",
    "EvalReport",
]
