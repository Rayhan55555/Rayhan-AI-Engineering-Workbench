import re
from datetime import datetime, timezone
from typing import List
from backend.app.rag.retriever import RetrievedChunk


class CrossScoringReranker:
    """
    Reranks candidate retrieved chunks using a 4-factor scoring model:
    - Cosine similarity score (40%)
    - Query term lexical overlap (30%)
    - Chunk length optimality (10%)
    - Recency bonus (20%)
    """

    @classmethod
    def rerank(
        cls,
        query: str,
        chunks: List[RetrievedChunk],
        top_n: int = 3,
    ) -> List[RetrievedChunk]:
        if not chunks:
            return []

        # Tokenize query into distinct lowercase words
        q_words = set(re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", query.lower()))

        reranked_items = []
        for ch in chunks:
            # Factor 1: Cosine similarity (40%)
            sim_score = min(1.0, max(0.0, ch.score))

            # Factor 2: Query term overlap (30%)
            c_words = set(re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", ch.content.lower()))
            overlap_ratio = len(q_words.intersection(c_words)) / max(1, len(q_words)) if q_words else 0.5
            overlap_score = min(1.0, max(0.0, overlap_ratio))

            # Factor 3: Length optimality (10%) - optimal range ~100-300 words
            word_count = len(ch.content.split())
            if 80 <= word_count <= 400:
                length_score = 1.0
            elif word_count < 80:
                length_score = max(0.3, word_count / 80.0)
            else:
                length_score = max(0.4, 1.0 - (word_count - 400) / 1000.0)

            # Factor 4: Recency bonus (20%)
            recency_score = 1.0
            created_str = ch.metadata.get("ingested_at") or ch.metadata.get("created_at")
            if created_str:
                try:
                    dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                    diff_days = (datetime.now(timezone.utc) - dt).days
                    if diff_days <= 1:
                        recency_score = 1.0
                    elif diff_days <= 7:
                        recency_score = 0.9
                    elif diff_days <= 30:
                        recency_score = 0.8
                    else:
                        recency_score = 0.6
                except Exception:
                    recency_score = 0.85

            # Weighted combination
            final_score = (
                (sim_score * 0.40)
                + (overlap_score * 0.30)
                + (length_score * 0.10)
                + (recency_score * 0.20)
            )

            # Create updated chunk with reranked score
            updated_chunk = ch.model_copy(update={"score": round(final_score, 4)})
            reranked_items.append(updated_chunk)

        # Sort descending by updated score
        reranked_items.sort(key=lambda x: x.score, reverse=True)
        return reranked_items[:top_n]
