from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TestReportSummary(BaseModel):
    overall_coverage: float
    total_tests: int
    gaps_found: int
    critical_gaps: int


class FullTestReport(BaseModel):
    execution_id: str
    agent: str = "testing-agent"
    status: str = "Completed"
    scope: str = "read_only"
    simulated: bool = False
    task_type: str
    summary: TestReportSummary
    coverage: Optional[Dict[str, Any]] = None
    gaps: Optional[List[Dict[str, Any]]] = None
    suggestions: Optional[List[Dict[str, Any]]] = None
    generated_tests: Optional[List[Dict[str, Any]]] = None
    failures: Optional[Dict[str, Any]] = None
    evidence: List[str]
    limitations: List[str]
    created_at: str
