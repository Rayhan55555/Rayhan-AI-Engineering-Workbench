from typing import Any, Dict, List
from pydantic import BaseModel


class EvaluationMetrics(BaseModel):
    relevance_score: float  # 0.0 - 1.0
    completeness_score: float  # 0.0 - 1.0
    safety_passed: bool
    format_valid: bool
    hallucination_risk: str  # 'low', 'medium', 'high'
    overall_quality: float  # 0.0 - 1.0
    notes: List[str]
