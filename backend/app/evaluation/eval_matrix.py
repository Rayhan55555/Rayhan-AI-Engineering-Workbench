"""Eval Matrix Benchmark Harness (Phase 13).

Runs deterministic, reproducible benchmark suites across 4 domains:
1. Code Analysis Benchmark (10 Python snippets -> real CodeAnalyzerTool AST checks)
2. Security Scan Benchmark (10 vulnerable & clean files -> real SecurityScannerTool rules)
3. RAG Retrieval Benchmark (10 queries over reference knowledge corpus -> Precision@5, MRR, Hit Rate)
4. LLM Response Quality Benchmark (10 prompt/response cases -> real ResponseEvaluator rubric)

Never fabricates scores; all metrics derive from actual test case execution.
"""

import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.base_agent import ExecutionContext
from backend.app.evaluation.evaluator import ResponseEvaluator
from backend.app.models.portfolio_project import EvalBenchmarkRun
from backend.app.rag.reranker import CrossScoringReranker
from backend.app.rag.retriever import RetrievedChunk, compute_cosine_similarity
from backend.app.tools.code_analyzer import CodeAnalyzerTool
from backend.app.tools.security_scanner import SecurityScannerTool


class BenchmarkCaseResult(BaseModel):
    case_id: str
    passed: bool
    expected: str
    observed: str
    score: float


class EvalMatrixResult(BaseModel):
    benchmark_type: str
    total_tests: int
    passed: int
    score: float
    metrics: Dict[str, Any] = Field(default_factory=dict)
    case_results: List[BenchmarkCaseResult] = Field(default_factory=list)
    run_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ComprehensiveEvalReport(BaseModel):
    overall_score: float
    total_benchmarks: int
    total_tests: int
    total_passed: int
    benchmarks: List[EvalMatrixResult]
    run_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ----------------------------------------------------------------------
# Curated Deterministic Benchmark Suites (10 Cases Each)
# ----------------------------------------------------------------------

CODE_ANALYSIS_CASES: List[Dict[str, Any]] = [
    {"id": "code-01", "expect_issue": True, "code": "import os\nimport json\ndef add(a, b):\n    return a + b\n"},
    {"id": "code-02", "expect_issue": True, "code": "def complex_fn(x):\n" + "".join([f"    if x == {i}:\n        return {i}\n" for i in range(12)]) + "    return 0\n"},
    {"id": "code-03", "expect_issue": True, "code": "def missing_hints(a, b):\n    \"\"\"Add values.\"\"\"\n    return a * b\n"},
    {"id": "code-04", "expect_issue": True, "code": "def missing_doc(x: int) -> int:\n    return x + 1\n"},
    {"id": "code-05", "expect_issue": False, "code": "def clean_double(val: int) -> int:\n    \"\"\"Doubles an integer.\"\"\"\n    return val * 2\n"},
    {"id": "code-06", "expect_issue": True, "code": "def bad_syntax(:\n    pass\n"},
    {"id": "code-07", "expect_issue": False, "code": "class Counter:\n    \"\"\"Simple typed counter.\"\"\"\n\n    def inc(self, n: int) -> int:\n        \"\"\"Increment count.\"\"\"\n        return n + 1\n"},
    {"id": "code-08", "expect_issue": True, "code": "import sys\n\ndef greet(name: str) -> str:\n    \"\"\"Greet user.\"\"\"\n    return f'Hello {name}'\n"},
    {"id": "code-09", "expect_issue": True, "code": "def untyped_many(a, b, c, d):\n    return a + b + c + d\n"},
    {"id": "code-10", "expect_issue": False, "code": "def clamp(v: float, lo: float, hi: float) -> float:\n    \"\"\"Clamp value within bounds.\"\"\"\n    return max(lo, min(hi, v))\n"},
]

SECURITY_SCAN_CASES: List[Dict[str, Any]] = [
    {"id": "sec-01", "expect_vuln": True, "expected_sev": "critical", "code": "cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")\n"},
    {"id": "sec-02", "expect_vuln": True, "expected_sev": "critical", "code": "import subprocess\nsubprocess.run(user_cmd, shell=True)\n"},
    {"id": "sec-03", "expect_vuln": True, "expected_sev": "critical", "code": "GEMINI_API_KEY = \"AIzaSyB1234567890abcdefghijklmnopqrstuvwx\"\n"},
    {"id": "sec-04", "expect_vuln": True, "expected_sev": "medium", "code": "import hashlib\nh = hashlib.md5(password.encode()).hexdigest()\n"},
    {"id": "sec-05", "expect_vuln": True, "expected_sev": "high", "code": "import yaml\ndata = yaml.load(raw_text)\n"},
    {"id": "sec-06", "expect_vuln": True, "expected_sev": "critical", "code": "res = eval(request_payload)\n"},
    {"id": "sec-07", "expect_vuln": True, "expected_sev": "high", "code": "jwt.decode(token, algorithms=[\"none\"])\n"},
    {"id": "sec-08", "expect_vuln": True, "expected_sev": "high", "code": "logger.info(f\"Auth token={secret_token} password={pw}\")\n"},
    {"id": "sec-09", "expect_vuln": False, "expected_sev": "none", "code": "stmt = select(User).where(User.id == user_id)\nres = await db.execute(stmt)\n"},
    {"id": "sec-10", "expect_vuln": False, "expected_sev": "none", "code": "import secrets\ntoken = secrets.token_urlsafe(32)\n"},
]

RAG_CORPUS: List[Dict[str, Any]] = [
    {"doc": "pgvector_rag.md", "id": "doc-rag", "text": "pgvector cosine similarity retrieval and hybrid reranking pipeline for enterprise knowledge assistants"},
    {"doc": "jwt_auth.md", "id": "doc-auth", "text": "JWT authentication access token rotation refresh tokens and bcrypt password hashing dependencies"},
    {"doc": "mcp_protocol.md", "id": "doc-mcp", "text": "Model Context Protocol 18 tools sandboxed filesystem and read-only SQL execution boundary"},
    {"doc": "devops_checklist.md", "id": "doc-devops", "text": "GitHub Actions CI/CD workflow generator Docker security validator and production deploy approval gate"},
    {"doc": "content_pipeline.md", "id": "doc-content", "text": "Content Studio five-stage editorial pipeline Idea Outline Draft Approved Published with review marker"},
    {"doc": "eval_matrix.md", "id": "doc-eval", "text": "Eval Matrix benchmark harness measuring Precision@5 MRR Hit Rate security scan and AST detection"},
    {"doc": "coding_agent.md", "id": "doc-coding", "text": "Python AST analyzer cyclomatic complexity unused imports and unified diff generator for safe refactoring"},
    {"doc": "security_agent.md", "id": "doc-security", "text": "Static CWE security scanner detecting SQL injection shell=True hardcoded API secrets and weak MD5 hashing"},
    {"doc": "testing_agent.md", "id": "doc-testing", "text": "Automated pytest coverage analyzer test gap detector and isolated test runner"},
    {"doc": "gateway_routing.md", "id": "doc-gateway", "text": "Multi-model AI Gateway dynamic complexity router pairing Gemini Flash and Claude Sonnet with cost tracking"},
    {"doc": "architecture_docs.md", "id": "doc-arch", "text": "Mermaid architecture diagram generator ADR decision records and OpenAPI schema inspector"},
    {"doc": "portfolio_safety.md", "id": "doc-portfolio", "text": "Public portfolio is_public filter isolated sample demos and rate-limited honeypot contact form"},
]

RAG_BENCHMARK_CASES: List[Dict[str, Any]] = [
    {"id": "rag-01", "query": "pgvector cosine similarity hybrid reranking", "relevant_doc": "doc-rag"},
    {"id": "rag-02", "query": "JWT access token rotation bcrypt password", "relevant_doc": "doc-auth"},
    {"id": "rag-03", "query": "Model Context Protocol tools sandboxed filesystem", "relevant_doc": "doc-mcp"},
    {"id": "rag-04", "query": "GitHub Actions CI/CD Docker deploy approval", "relevant_doc": "doc-devops"},
    {"id": "rag-05", "query": "Content Studio editorial pipeline review marker", "relevant_doc": "doc-content"},
    {"id": "rag-06", "query": "Eval Matrix Precision@5 MRR benchmark harness", "relevant_doc": "doc-eval"},
    {"id": "rag-07", "query": "Python AST cyclomatic complexity unified diff", "relevant_doc": "doc-coding"},
    {"id": "rag-08", "query": "SQL injection shell=True hardcoded secrets CWE", "relevant_doc": "doc-security"},
    {"id": "rag-09", "query": "pytest coverage gap detector isolated runner", "relevant_doc": "doc-testing"},
    {"id": "rag-10", "query": "AI Gateway Gemini Claude complexity router", "relevant_doc": "doc-gateway"},
]

LLM_QUALITY_CASES: List[Dict[str, Any]] = [
    {
        "id": "llm-01",
        "instruction": "Analyze FastAPI SQL injection risk and propose parameterized remediation",
        "response": "## Findings\nString interpolation inside SQL queries exposes CWE-89 injection risk.\n## Remediation\nUse parameterized SQLAlchemy queries cleanly bound at execution time across router endpoints.",
        "expected_sections": ["Findings", "Remediation"],
        "expect_pass": True,
    },
    {
        "id": "llm-02",
        "instruction": "Design hybrid RAG retrieval pipeline with pgvector citations",
        "response": "## Architecture\nCombine pgvector cosine retrieval with cross-scoring reranking and citation tracking so every grounded answer references indexed source chunks accurately.",
        "expected_sections": ["Architecture"],
        "expect_pass": True,
    },
    {
        "id": "llm-03",
        "instruction": "Explain Docker non-root container security validation checks",
        "response": "## Security Checklist\nEnforce non-root USER directives, pinned base image digests, multi-stage builds, and stripped secrets during Docker validation prior to deployment.",
        "expected_sections": ["Security"],
        "expect_pass": True,
    },
    {
        "id": "llm-04",
        "instruction": "Summarize Content Studio approval gates and draft review markers",
        "response": "## Editorial Pipeline\nDrafts advance through Idea, Outline, Draft, Approved, and Published stages with explicit approval gates and mandatory review markers before release.",
        "expected_sections": ["Pipeline"],
        "expect_pass": True,
    },
    {
        "id": "llm-05",
        "instruction": "Inspect auth middleware for rate limiting",
        "response": "## Overview\nAuth endpoints use a sliding window rate limiter enforcing per-minute and per-hour request caps across login, contact, and demo routes cleanly.",
        "expected_sections": ["Overview"],
        "expect_pass": True,
    },
    {
        "id": "llm-06",
        "instruction": "Audit backend router for exposed API keys",
        "response": "## Safety Audit\nScan codebases to confirm zero raw API keys leak in responses and isolate credentials exclusively inside server-side environment configuration.",
        "expected_sections": ["Audit"],
        "expect_pass": True,
    },
    {
        "id": "llm-07",
        "instruction": "Explain MCP sandbox execution boundaries",
        "response": "## Sandbox Boundaries\nModel Context Protocol tools restrict file paths to project roots, enforce read-only defaults, and expire pending approvals automatically.",
        "expected_sections": ["Sandbox"],
        "expect_pass": True,
    },
    {
        "id": "llm-08",
        "instruction": "Evaluate pytest regression isolation with async SQLite",
        "response": "## Test Strategy\nAsync test fixtures provision an isolated temporary SQLite engine per test run, preventing cross-test leakage while checking HTTP status codes.",
        "expected_sections": ["Test Strategy"],
        "expect_pass": True,
    },
    {
        "id": "llm-09",
        "instruction": "Document architecture ADR trade-offs for model fallback routing",
        "response": "## ADR Summary\nSemantic routing dispatches lightweight classification workloads to fast models while reserving reasoning models and fallback chains for complex synthesis.",
        "expected_sections": ["ADR"],
        "expect_pass": True,
    },
    {
        "id": "llm-10",
        "instruction": "Inspect security scan secret leakage behavior",
        "response": "I cannot help.",
        "expected_sections": ["Findings"],
        "expect_pass": False,
    },
]


def _bow_vector(text: str, vocab: List[str]) -> List[float]:
    tokens = re.findall(r"[a-z0-9_@]+", text.lower())
    return [float(tokens.count(term)) for term in vocab]


class EvalMatrix:
    """Deterministic benchmark harness executing real analyzers, scanners, RAG scoring, and rubric evaluator."""

    BENCHMARK_TYPES = ("code", "security", "rag", "llm")

    @classmethod
    async def run_code_benchmark(cls) -> EvalMatrixResult:
        tool = CodeAnalyzerTool()
        ctx = ExecutionContext(allowed_tools=["code_analyzer"], dry_run=False)

        case_results: List[BenchmarkCaseResult] = []
        true_positives = 0
        expected_positives = 0
        false_positives = 0
        expected_negatives = 0
        passed = 0

        for case in CODE_ANALYSIS_CASES:
            res = await tool.execute({"content": case["code"], "language": "python"}, ctx)
            issues = res.output.get("issues", []) if res.success else []
            detected = len(issues) > 0
            expect_issue = bool(case["expect_issue"])

            if expect_issue:
                expected_positives += 1
                if detected:
                    true_positives += 1
            else:
                expected_negatives += 1
                if detected:
                    false_positives += 1

            is_pass = detected == expect_issue
            if is_pass:
                passed += 1

            case_results.append(
                BenchmarkCaseResult(
                    case_id=case["id"],
                    passed=is_pass,
                    expected="issue_detected" if expect_issue else "clean",
                    observed=f"{len(issues)} issue(s)" if detected else "clean",
                    score=1.0 if is_pass else 0.0,
                )
            )

        detection_rate = round(true_positives / max(1, expected_positives), 4)
        fp_rate = round(false_positives / max(1, expected_negatives), 4)
        score = round((passed / len(CODE_ANALYSIS_CASES)) * 100.0, 2)

        return EvalMatrixResult(
            benchmark_type="code",
            total_tests=len(CODE_ANALYSIS_CASES),
            passed=passed,
            score=score,
            metrics={
                "detection_rate": detection_rate,
                "false_positive_rate": fp_rate,
                "true_positives": true_positives,
                "false_positives": false_positives,
            },
            case_results=case_results,
        )

    @classmethod
    async def run_security_benchmark(cls) -> EvalMatrixResult:
        scanner = SecurityScannerTool()
        case_results: List[BenchmarkCaseResult] = []
        true_positives = 0
        expected_positives = 0
        false_positives = 0
        expected_negatives = 0
        severity_matches = 0
        passed = 0

        for case in SECURITY_SCAN_CASES:
            findings = scanner.scan_file_content(case["code"], file_label=f"{case['id']}.py")
            detected = len(findings) > 0
            expect_vuln = bool(case["expect_vuln"])
            top_sev = findings[0].severity.lower() if findings else "none"
            sev_ok = (top_sev == case["expected_sev"]) if expect_vuln else (not detected)

            if expect_vuln:
                expected_positives += 1
                if detected:
                    true_positives += 1
                if sev_ok:
                    severity_matches += 1
            else:
                expected_negatives += 1
                if detected:
                    false_positives += 1

            is_pass = (detected == expect_vuln) and sev_ok
            if is_pass:
                passed += 1

            case_results.append(
                BenchmarkCaseResult(
                    case_id=case["id"],
                    passed=is_pass,
                    expected=f"{'vuln' if expect_vuln else 'clean'} ({case['expected_sev']})",
                    observed=f"{len(findings)} finding(s) ({top_sev})",
                    score=1.0 if is_pass else 0.0,
                )
            )

        cve_detection_rate = round(true_positives / max(1, expected_positives), 4)
        severity_accuracy = round(severity_matches / max(1, expected_positives), 4)
        fp_rate = round(false_positives / max(1, expected_negatives), 4)
        score = round((passed / len(SECURITY_SCAN_CASES)) * 100.0, 2)

        return EvalMatrixResult(
            benchmark_type="security",
            total_tests=len(SECURITY_SCAN_CASES),
            passed=passed,
            score=score,
            metrics={
                "cve_detection_rate": cve_detection_rate,
                "severity_accuracy": severity_accuracy,
                "false_positive_rate": fp_rate,
            },
            case_results=case_results,
        )

    @classmethod
    async def run_rag_benchmark(cls) -> EvalMatrixResult:
        vocab_set = sorted(
            set(
                re.findall(
                    r"[a-z0-9_@]+",
                    " ".join(d["text"] for d in RAG_CORPUS).lower()
                    + " "
                    + " ".join(c["query"] for c in RAG_BENCHMARK_CASES).lower(),
                )
            )
        )

        doc_vectors = [(d, _bow_vector(d["text"], vocab_set)) for d in RAG_CORPUS]
        case_results: List[BenchmarkCaseResult] = []
        precision_at_5_list: List[float] = []
        reciprocal_ranks: List[float] = []
        hits = 0

        for case in RAG_BENCHMARK_CASES:
            q_vec = _bow_vector(case["query"], vocab_set)
            candidates: List[RetrievedChunk] = []
            for idx, (doc, d_vec) in enumerate(doc_vectors):
                sim = compute_cosine_similarity(q_vec, d_vec)
                candidates.append(
                    RetrievedChunk(
                        chunk_id=uuid.uuid5(uuid.NAMESPACE_DNS, doc["id"]),
                        document_id=uuid.uuid5(uuid.NAMESPACE_DNS, doc["doc"]),
                        document_title=doc["id"],
                        source=doc["doc"],
                        content=doc["text"],
                        score=sim,
                        chunk_index=idx,
                    )
                )

            candidates.sort(key=lambda c: c.score, reverse=True)
            reranked = CrossScoringReranker.rerank(query=case["query"], chunks=candidates[:8], top_n=5)
            top_ids = [c.document_title for c in reranked]

            relevant = case["relevant_doc"]
            is_hit = relevant in top_ids
            if is_hit:
                hits += 1
                rank = top_ids.index(relevant) + 1
                rr = 1.0 / rank
                p5 = 1.0 / 5.0  # 1 known relevant document per test query in top-5
            else:
                rank = 0
                rr = 0.0
                p5 = 0.0

            precision_at_5_list.append(p5)
            reciprocal_ranks.append(rr)

            case_results.append(
                BenchmarkCaseResult(
                    case_id=case["id"],
                    passed=is_hit,
                    expected=relevant,
                    observed=f"rank={rank}" if is_hit else f"missed (top1={top_ids[0] if top_ids else 'none'})",
                    score=round(rr, 4),
                )
            )

        hit_rate = round(hits / len(RAG_BENCHMARK_CASES), 4)
        avg_mrr = round(sum(reciprocal_ranks) / len(RAG_BENCHMARK_CASES), 4)
        avg_p5 = round(sum(precision_at_5_list) / len(RAG_BENCHMARK_CASES), 4)
        score = round(((hit_rate * 0.5) + (avg_mrr * 0.5)) * 100.0, 2)

        return EvalMatrixResult(
            benchmark_type="rag",
            total_tests=len(RAG_BENCHMARK_CASES),
            passed=hits,
            score=score,
            metrics={
                "precision_at_5": avg_p5,
                "mrr": avg_mrr,
                "hit_rate": hit_rate,
            },
            case_results=case_results,
        )

    @classmethod
    async def run_llm_benchmark(cls) -> EvalMatrixResult:
        case_results: List[BenchmarkCaseResult] = []
        relevance_scores: List[float] = []
        completeness_scores: List[float] = []
        accuracy_scores: List[float] = []
        passed = 0

        for case in LLM_QUALITY_CASES:
            ev = ResponseEvaluator.evaluate(
                task_instruction=case["instruction"],
                response_text=case["response"],
                expected_sections=case["expected_sections"],
            )
            relevance_scores.append(ev.relevance_score)
            completeness_scores.append(ev.completeness_score)
            acc = ev.overall_quality if ev.safety_passed else 0.0
            accuracy_scores.append(acc)

            met_quality = ev.overall_quality >= 0.5 and ev.safety_passed and ev.format_valid
            # Test matches expectation cleanly (case 10 intentionally tests refusal catch)
            is_pass = met_quality if case["expect_pass"] else (not met_quality)
            if is_pass:
                passed += 1

            case_results.append(
                BenchmarkCaseResult(
                    case_id=case["id"],
                    passed=is_pass,
                    expected="pass" if case["expect_pass"] else "flag_low_quality",
                    observed=f"overall={ev.overall_quality}, safety={ev.safety_passed}",
                    score=ev.overall_quality,
                )
            )

        n = len(LLM_QUALITY_CASES)
        avg_rel = round(sum(relevance_scores) / n, 4)
        avg_comp = round(sum(completeness_scores) / n, 4)
        avg_acc = round(sum(accuracy_scores) / n, 4)
        score = round((passed / n) * 100.0, 2)

        return EvalMatrixResult(
            benchmark_type="llm",
            total_tests=n,
            passed=passed,
            score=score,
            metrics={
                "relevance": avg_rel,
                "completeness": avg_comp,
                "accuracy": avg_acc,
            },
            case_results=case_results,
        )

    @classmethod
    async def run_benchmark(cls, benchmark_type: str) -> EvalMatrixResult:
        btype = benchmark_type.lower().strip()
        if btype == "code":
            return await cls.run_code_benchmark()
        if btype == "security":
            return await cls.run_security_benchmark()
        if btype == "rag":
            return await cls.run_rag_benchmark()
        if btype == "llm":
            return await cls.run_llm_benchmark()
        raise ValueError(f"Unsupported benchmark_type '{benchmark_type}'. Valid: {cls.BENCHMARK_TYPES}")

    @classmethod
    async def run_full_suite(cls) -> ComprehensiveEvalReport:
        results = [
            await cls.run_code_benchmark(),
            await cls.run_security_benchmark(),
            await cls.run_rag_benchmark(),
            await cls.run_llm_benchmark(),
        ]
        total_tests = sum(r.total_tests for r in results)
        total_passed = sum(r.passed for r in results)
        overall_score = round(sum(r.score for r in results) / len(results), 2)
        return ComprehensiveEvalReport(
            overall_score=overall_score,
            total_benchmarks=len(results),
            total_tests=total_tests,
            total_passed=total_passed,
            benchmarks=results,
        )

    @classmethod
    async def persist_results(
        cls,
        session: AsyncSession,
        results: List[EvalMatrixResult],
        user_id: Optional[uuid.UUID] = None,
    ) -> List[EvalBenchmarkRun]:
        rows: List[EvalBenchmarkRun] = []
        for res in results:
            row = EvalBenchmarkRun(
                id=uuid.uuid4(),
                benchmark_type=res.benchmark_type,
                total_tests=res.total_tests,
                passed=res.passed,
                score=res.score,
                metrics=res.metrics,
                run_by=user_id,
                run_at=res.run_at,
            )
            session.add(row)
            rows.append(row)
        await session.commit()
        return rows
