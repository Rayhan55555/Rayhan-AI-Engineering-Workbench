"""Eval Matrix Agent (slug: eval-matrix) full implementation for Phase 13."""

import json
from typing import List
from backend.app.agents.base_agent import (
    AgentResult,
    AgentTask,
    Artifact,
    BaseAgent,
    CapabilityDescription,
    Evidence,
    ExecutionContext,
    ValidationResult,
)
import backend.app.database as db_module
from backend.app.evaluation.eval_matrix import EvalMatrix, EvalMatrixResult


class EvalMatrixAgent(BaseAgent):
    """Runs deterministic Code, Security, RAG, and LLM quality benchmarks and persists metrics."""

    slug = "eval-matrix"
    name = "Eval & Benchmark Harness"
    purpose = (
        "Executes deterministic regression benchmarks across Code Analysis AST rules, "
        "Security CVE/pattern detection, RAG Precision@5/MRR retrieval, and LLM Response Quality."
    )
    phase = 13
    version = "1.0.0"
    allowed_tools = [
        "code_analysis_benchmark",
        "security_scan_benchmark",
        "rag_retrieval_benchmark",
        "llm_quality_benchmark",
    ]
    required_permissions = ["READ_ONLY", "SUGGEST"]
    limitations = [
        "Benchmarks evaluate curated 10-case deterministic test suites per domain rather than external unseen customer corpora",
        "RAG retrieval benchmark runs against the bundled reference corpus using bag-of-words cosine + cross-scoring",
        "No fabricated or extrapolated performance scores",
    ]

    async def validate_input(self, task: AgentTask) -> ValidationResult:
        if not task.instruction or len(task.instruction.strip()) < 3:
            return ValidationResult(valid=False, error="Instruction must be at least 3 characters.")
        return ValidationResult(valid=True)

    async def execute(self, task: AgentTask, context: ExecutionContext) -> AgentResult:
        inst = task.instruction.lower().strip()
        evidence: List[Evidence] = []
        artifacts: List[Artifact] = []

        results_to_persist: List[EvalMatrixResult] = []

        if "full" in inst or "suite" in inst or "all" in inst:
            report = await EvalMatrix.run_full_suite()
            results_to_persist = list(report.benchmarks)
            payload_json = report.model_dump(mode="json")
            output_summary = (
                f"### Eval Matrix — Full Benchmark Suite\n\n"
                f"- **Overall Score**: `{report.overall_score}/100`\n"
                f"- **Total Passed**: `{report.total_passed}/{report.total_tests}` across {report.total_benchmarks} suites\n\n"
                + "\n".join(
                    f"- **{b.benchmark_type.upper()}**: `{b.score}/100` ({b.passed}/{b.total_tests}) — `{json.dumps(b.metrics)}`"
                    for b in report.benchmarks
                )
            )
            artifact_name = "eval-matrix-full-report.json"
            evidence.append(
                Evidence(
                    source="eval_matrix",
                    snippet=f"Executed 4 benchmark suites ({report.total_passed}/{report.total_tests} passed, score={report.overall_score})",
                    confidence=1.0,
                )
            )
        else:
            if "security" in inst or "cve" in inst or "vuln" in inst:
                btype = "security"
            elif "rag" in inst or "retrieval" in inst or "precision" in inst:
                btype = "rag"
            elif "llm" in inst or "quality" in inst or "response" in inst:
                btype = "llm"
            else:
                btype = "code"

            single = await EvalMatrix.run_benchmark(btype)
            results_to_persist = [single]
            payload_json = single.model_dump(mode="json")
            output_summary = (
                f"### Eval Matrix — `{btype.upper()}` Benchmark\n\n"
                f"- **Score**: `{single.score}/100`\n"
                f"- **Passed**: `{single.passed}/{single.total_tests}`\n"
                f"- **Metrics**: `{json.dumps(single.metrics)}`"
            )
            artifact_name = f"eval-matrix-{btype}.json"
            evidence.append(
                Evidence(
                    source=f"eval_matrix.{btype}",
                    snippet=f"Benchmark '{btype}' completed: {single.passed}/{single.total_tests} passed (score={single.score})",
                    confidence=1.0,
                )
            )

        # Persist results to DB
        persisted_count = 0
        try:
            async with db_module.AsyncSessionLocal() as session:
                rows = await EvalMatrix.persist_results(
                    session=session,
                    results=results_to_persist,
                    user_id=task.requested_by,
                )
                persisted_count = len(rows)
        except Exception:
            persisted_count = 0

        if persisted_count:
            evidence.append(
                Evidence(
                    source="eval_benchmark_runs",
                    snippet=f"Persisted {persisted_count} benchmark run record(s) to database.",
                    confidence=1.0,
                )
            )

        artifacts.append(
            Artifact(
                name=artifact_name,
                artifact_type="benchmark_report",
                content=json.dumps(payload_json, indent=2, default=str),
                metadata={"persisted_runs": persisted_count},
            )
        )

        return AgentResult(
            success=True,
            output=output_summary,
            artifacts=artifacts,
            evidence=evidence,
            limitations=self.limitations,
            simulated=False,
        )

    async def describe_capabilities(self) -> CapabilityDescription:
        return CapabilityDescription(
            slug=self.slug,
            name=self.name,
            purpose=self.purpose,
            phase=self.phase,
            version=self.version,
            allowed_tools=self.allowed_tools,
            required_permissions=self.required_permissions,
            limitations=self.limitations,
        )
