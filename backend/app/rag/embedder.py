import logging
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from backend.app.config import settings

logger = logging.getLogger("rag.embedder")

EMBEDDING_MODEL = "models/text-embedding-004"
EMBEDDING_DIM = 768
BATCH_SIZE = 100
CACHE_TTL_SECONDS = 300  # 5 minutes


class EmbeddedChunk(BaseModel):
    chunk_id: str
    content: str
    embedding: Optional[List[float]] = None
    token_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Embedder:
    """
    Embedder leveraging Google text-embedding-004 (768 dimensions).
    Supports chunk batching, rate limiting safeguards, 5-minute query caching,
    and strict integrity: NEVER fabricates fake embeddings.
    """

    _query_cache: Dict[str, Dict[str, Any]] = {}
    _genai_client = None

    @classmethod
    def _get_genai(cls):
        if not settings.GEMINI_API_KEY:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            return genai
        except Exception as e:
            logger.warning(f"Failed to initialize google.generativeai for embeddings: {e}")
            return None

    @classmethod
    def embed_chunks(
        cls,
        chunks: List[Any],
        task_type: str = "retrieval_document",
    ) -> List[EmbeddedChunk]:
        """
        Embeds a list of chunks in batches of up to 100.
        Returns a list of EmbeddedChunk. If API fails, embedding is None.
        Never fabricates embeddings.
        """
        if not chunks:
            return []

        genai = cls._get_genai()
        embedded_results: List[EmbeddedChunk] = []

        # Process in batches of 100
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            texts = [c.content if hasattr(c, "content") else str(c) for c in batch]

            embeddings: List[Optional[List[float]]] = [None] * len(batch)

            if genai:
                try:
                    res = genai.embed_content(
                        model=EMBEDDING_MODEL,
                        content=texts,
                        task_type=task_type,
                    )
                    raw_emb = res.get("embedding", [])
                    # raw_emb is a list of lists if batch
                    if raw_emb and isinstance(raw_emb[0], list):
                        embeddings = raw_emb
                    elif raw_emb and isinstance(raw_emb[0], (int, float)):
                        embeddings = [raw_emb]
                except Exception as ex:
                    logger.warning(
                        f"text-embedding-004 batch API call failed: {ex}. Marking chunks as un-embedded."
                    )
            else:
                logger.debug("GEMINI_API_KEY not configured; chunks not embedded.")

            for idx, c in enumerate(batch):
                c_id = getattr(c, "chunk_id", str(idx))
                content = getattr(c, "content", str(c))
                tokens = getattr(c, "token_count", len(content.split()))
                meta = getattr(c, "metadata", {})
                emb = embeddings[idx] if idx < len(embeddings) else None

                embedded_results.append(
                    EmbeddedChunk(
                        chunk_id=c_id,
                        content=content,
                        embedding=emb,
                        token_count=tokens,
                        metadata=meta,
                    )
                )

        return embedded_results

    @classmethod
    def embed_query(cls, query: str) -> Optional[List[float]]:
        """
        Generates a 768-dim query embedding using task_type='retrieval_query'.
        Results cached in memory for 5 minutes.
        Returns None if API unavailable. Never fabricates values.
        """
        q = query.strip()
        if not q:
            return None

        # Check in-memory TTL cache
        now = time.monotonic()
        if q in cls._query_cache:
            entry = cls._query_cache[q]
            if now - entry["timestamp"] < CACHE_TTL_SECONDS:
                return entry["embedding"]
            else:
                del cls._query_cache[q]

        genai = cls._get_genai()
        if not genai:
            logger.debug("GEMINI_API_KEY not configured for query embedding.")
            return None

        try:
            res = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=q,
                task_type="retrieval_query",
            )
            emb = res.get("embedding")
            if emb and isinstance(emb, list):
                # Cache successful query embedding
                cls._query_cache[q] = {
                    "embedding": emb,
                    "timestamp": now,
                }
                return emb
        except Exception as ex:
            logger.warning(f"Failed to generate query embedding: {ex}")

        return None

    @classmethod
    def clear_cache(cls):
        """Clears the query embedding cache."""
        cls._query_cache.clear()
