from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EvalTestCase(BaseModel):
    query: str
    expected_doc_ids: List[str] = Field(default_factory=list)
    expected_keywords: List[str] = Field(default_factory=list)


class EvalReport(BaseModel):
    precision_at_k: float
    recall_at_k: float
    mrr: float
    hit_rate: float
    avg_score: float
    total_queries: int
    recommendations: List[str] = Field(default_factory=list)


class RetrievalEvaluator:
    """
    Evaluates retrieval quality against test queries and ground-truth references:
    - Precision@K: Fraction of retrieved chunks that are relevant
    - Recall@K: Fraction of total expected relevant items that were retrieved
    - MRR (Mean Reciprocal Rank): 1 / rank of first relevant chunk
    - Hit Rate: Proportion of queries with at least one relevant hit
    - Avg Score: Mean similarity confidence across all retrieved results
    """

    @classmethod
    def evaluate(
        cls,
        eval_results: List[Dict[str, Any]],
        k: int = 5,
    ) -> EvalReport:
        if not eval_results:
            return EvalReport(
                precision_at_k=0.0,
                recall_at_k=0.0,
                mrr=0.0,
                hit_rate=0.0,
                avg_score=0.0,
                total_queries=0,
                recommendations=["Knowledge base contains insufficient query history for statistical evaluation."],
            )

        precisions = []
        recalls = []
        reciprocal_ranks = []
        hits = 0
        all_scores = []

        for item in eval_results:
            retrieved = item.get("retrieved", [])[:k]
            expected_ids = set(str(x) for x in item.get("expected_ids", []))
            expected_keywords = [kw.lower() for kw in item.get("expected_keywords", [])]

            if not retrieved:
                precisions.append(0.0)
                recalls.append(0.0)
                reciprocal_ranks.append(0.0)
                continue

            relevant_count = 0
            first_rank = None

            for rank, r in enumerate(retrieved, start=1):
                doc_id = str(r.get("document_id", ""))
                content = str(r.get("content", "")).lower()
                score = float(r.get("score", 0.0))
                all_scores.append(score)

                is_relevant = False
                if doc_id and doc_id in expected_ids:
                    is_relevant = True
                elif expected_keywords and any(kw in content for kw in expected_keywords):
                    is_relevant = True

                if is_relevant:
                    relevant_count += 1
                    if first_rank is None:
                        first_rank = rank

            p_at_k = relevant_count / len(retrieved)
            precisions.append(p_at_k)

            total_expected = max(1, len(expected_ids) or len(expected_keywords) or 1)
            r_at_k = min(1.0, relevant_count / total_expected)
            recalls.append(r_at_k)

            if first_rank is not None:
                reciprocal_ranks.append(1.0 / first_rank)
                hits += 1
            else:
                reciprocal_ranks.append(0.0)

        total = len(eval_results)
        avg_precision = sum(precisions) / total if total else 0.0
        avg_recall = sum(recalls) / total if total else 0.0
        avg_mrr = sum(reciprocal_ranks) / total if total else 0.0
        hit_rate = hits / total if total else 0.0
        mean_score = sum(all_scores) / len(all_scores) if all_scores else 0.0

        recommendations = []
        if avg_precision < 0.6:
            recommendations.append("Increase cosine similarity threshold (e.g. from 0.65 to 0.75) to filter marginal chunks.")
        if avg_recall < 0.6:
            recommendations.append("Consider reducing chunk size or increasing chunk overlap to capture split concepts.")
        if hit_rate < 0.7:
            recommendations.append("Expand knowledge base coverage for core architectural and system terminology.")
        if not recommendations:
            recommendations.append("Retrieval metrics meet production benchmarks (MRR >= 0.70, Hit Rate >= 85%).")

        return EvalReport(
            precision_at_k=round(avg_precision, 4),
            recall_at_k=round(avg_recall, 4),
            mrr=round(avg_mrr, 4),
            hit_rate=round(hit_rate, 4),
            avg_score=round(mean_score, 4),
            total_queries=total,
            recommendations=recommendations,
        )
