"""Integration and benchmark tests for Phase 13 EvalMatrix & EvalMatrixAgent."""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.base_agent import AgentTask, ExecutionContext, TaskScope
from backend.app.agents.implementations.eval_matrix_agent import EvalMatrixAgent
from backend.app.evaluation.eval_matrix import EvalMatrix
from backend.app.models.portfolio_project import EvalBenchmarkRun


@pytest.mark.asyncio
async def test_eval_matrix_code_benchmark():
    """Code analysis benchmark runs 10 AST test cases and returns detection & FP metrics."""
    res = await EvalMatrix.run_benchmark("code")
    assert res.benchmark_type == "code"
    assert res.total_tests == 10
    assert 0.0 <= res.score <= 100.0
    assert "detection_rate" in res.metrics
    assert "false_positive_rate" in res.metrics
    assert res.metrics["detection_rate"] > 0.7


@pytest.mark.asyncio
async def test_eval_matrix_security_benchmark():
    """Security scan benchmark detects injected CWE patterns and evaluates severity accuracy."""
    res = await EvalMatrix.run_benchmark("security")
    assert res.benchmark_type == "security"
    assert res.total_tests == 10
    assert 0.0 <= res.score <= 100.0
    assert "cve_detection_rate" in res.metrics
    assert "severity_accuracy" in res.metrics
    assert res.metrics["cve_detection_rate"] >= 0.75


@pytest.mark.asyncio
async def test_eval_matrix_rag_benchmark():
    """RAG retrieval benchmark computes Precision@5, MRR, and Hit Rate over 10 queries."""
    res = await EvalMatrix.run_benchmark("rag")
    assert res.benchmark_type == "rag"
    assert res.total_tests == 10
    assert 0.0 <= res.score <= 100.0
    assert res.metrics["hit_rate"] >= 0.8
    assert res.metrics["mrr"] > 0.5
    assert res.metrics["precision_at_5"] > 0.0


@pytest.mark.asyncio
async def test_eval_matrix_full_suite_and_db_persistence(db_session: AsyncSession):
    """Full benchmark suite runs all 4 suites and persists EvalBenchmarkRun records in DB."""
    report = await EvalMatrix.run_full_suite()
    assert report.total_benchmarks == 4
    assert report.total_tests == 40
    types = {b.benchmark_type for b in report.benchmarks}
    assert types == {"code", "security", "rag", "llm"}
    assert 0.0 <= report.overall_score <= 100.0

    # Persist into DB explicitly and verify rows
    rows = await EvalMatrix.persist_results(db_session, report.benchmarks)
    assert len(rows) == 4

    db_res = await db_session.execute(select(EvalBenchmarkRun))
    stored = list(db_res.scalars().all())
    assert len(stored) >= 4
    assert {r.benchmark_type for r in stored}.issuperset({"code", "security", "rag", "llm"})


@pytest.mark.asyncio
async def test_eval_matrix_agent_execution(db_session: AsyncSession):
    """EvalMatrixAgent executes full benchmark suite with simulated=False and persists DB runs."""
    agent = EvalMatrixAgent()
    task = AgentTask(
        agent_slug="eval-matrix",
        instruction="run full benchmark suite",
        scope=TaskScope.read_only,
        requested_by=uuid.uuid4(),
    )
    ctx = ExecutionContext(allowed_tools=agent.allowed_tools, dry_run=False)
    result = await agent.execute(task, ctx)

    assert result.success is True
    assert result.simulated is False
    assert "Overall Score" in result.output
    assert len(result.artifacts) == 1
    assert result.artifacts[0].name == "eval-matrix-full-report.json"

    # Confirm agent persisted 4 rows via AsyncSessionLocal inside execute()
    db_res = await db_session.execute(select(EvalBenchmarkRun))
    assert len(list(db_res.scalars().all())) >= 4
