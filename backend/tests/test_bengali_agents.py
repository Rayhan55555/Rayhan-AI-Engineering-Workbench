"""Automated tests for Bengali Agent Profiles & Bilingual Execution Outputs."""

import asyncio
import json
import pytest
from httpx import AsyncClient

from backend.app.agents.bengali_presenter import (
    BENGALI_AGENT_PROFILES,
    build_bengali_report,
    to_bn_digits,
)


ALL_NINE_AGENT_SLUGS = [
    "arch-sentinel",
    "security-agent",
    "testing-agent",
    "architecture-agent",
    "documentation-agent",
    "rag-engine-v1",
    "devops-agent",
    "masterclass-synth",
    "eval-matrix",
]


def test_all_nine_bengali_profiles_defined():
    for slug in ALL_NINE_AGENT_SLUGS:
        profile = BENGALI_AGENT_PROFILES.get(slug)
        assert profile is not None, f"Missing Bengali profile for {slug}"
        assert profile["name_bn"].strip()
        assert profile["work_bn"].strip()
        assert len(profile["when_to_use_bn"]) >= 2


def test_to_bn_digits_conversion():
    assert to_bn_digits(3) == "৩"
    assert to_bn_digits("196/196") == "১৯৬/১৯৬"
    assert to_bn_digits(87.5) == "৮৭.৫"


def test_bengali_report_coding_agent_real_counts():
    sample = json.dumps(
        {
            "target_file": "backend/app/main.py",
            "analysis": {
                "file_path": "backend/app/main.py",
                "functions": ["health", "lifespan"],
                "classes": ["AppConfig"],
                "issues": [
                    {"line": 12, "message": "Unused import"},
                    {"line": 44, "message": "Bare except"},
                    {"line": 89, "message": "Long function"},
                ],
            },
        }
    )
    rep = build_bengali_report(
        agent_slug="arch-sentinel",
        instruction="Inspect backend/app/main.py",
        scope="read_only",
        status_value="Completed",
        output=sample,
        simulated=False,
    )
    assert rep["language"] == "bn"
    assert rep["agent_name_bn"] == "কোডিং সহকারী"
    assert "বিশ্লেষণ সম্পন্ন। ৩টি সমস্যা পাওয়া গেছে।" == rep["summary_bn"]
    assert len(rep["findings"]) >= 3
    assert len(rep["recommendations"]) >= 1
    assert len(rep["limitations"]) >= 1


def test_bengali_report_all_nine_agents_completed():
    sample_outputs = {
        "arch-sentinel": json.dumps({"action": "suggest_fix", "target_file": "a.py", "diff": "+pass"}),
        "security-agent": json.dumps({"scan_type": "remediation_guidance", "recommendations": [{"finding_id": "INJ-001", "title": "SQL Injection", "severity": "Critical", "remediation": "Use ORM"}]}),
        "testing-agent": json.dumps({"task_type": "coverage_analysis", "summary": {"overall_coverage": 84.5, "total_files": 20, "files_below_50": 1, "critical_gaps": []}}),
        "architecture-agent": json.dumps({"mermaid": "graph TD; A-->B;", "modules": ["api", "db"]}),
        "documentation-agent": json.dumps({"documented_endpoints": 42, "total_endpoints": 45, "coverage_percentage": 93.3, "quality_score": 91}),
        "rag-engine-v1": json.dumps({"citations": [{"document": "spec.md"}], "answer": "JWT Auth used."}),
        "devops-agent": "### Deployment Readiness Evaluation: **READY** (100%)",
        "masterclass-synth": "# [REVIEW REQUIRED] Hybrid RAG Architecture Guide\n\nDetailed breakdown.",
        "eval-matrix": "### Eval Matrix — `FULL` Benchmark Suite\n- **Overall Score**: `96/100`\n- **Total Passed**: `39/40`",
    }
    for slug in ALL_NINE_AGENT_SLUGS:
        rep = build_bengali_report(
            agent_slug=slug,
            instruction=f"Run check for {slug}",
            scope="read_only",
            status_value="Completed",
            output=sample_outputs[slug],
            simulated=False,
        )
        assert rep["language"] == "bn"
        assert rep["summary_bn"]
        assert rep["what_agent_did"]
        assert isinstance(rep["findings"], list) and len(rep["findings"]) >= 1
        assert isinstance(rep["recommendations"], list) and len(rep["recommendations"]) >= 1
        assert isinstance(rep["limitations"], list) and len(rep["limitations"]) >= 1


def test_bengali_report_pending_and_failed_states():
    pending_impl = build_bengali_report(
        agent_slug="arch-sentinel",
        instruction="Run tests",
        scope="implement",
        status_value="Pending",
    )
    assert "অনুমোদন" in pending_impl["summary_bn"]

    failed = build_bengali_report(
        agent_slug="security-agent",
        instruction="Patch secrets",
        scope="implement",
        status_value="Failed",
        error_message="Permission denied: security fixes must be reviewed manually",
    )
    assert "সম্পন্ন করা যায়নি" in failed["summary_bn"]
    assert len(failed["findings"]) >= 1


@pytest.mark.asyncio
async def test_execution_api_returns_bilingual_bn_report(
    client: AsyncClient, auth_headers: dict, super_auth_headers: dict
):
    await client.post("/api/v1/agents/seed", headers=super_auth_headers)
    await client.post("/api/v1/agents/arch-sentinel/configure", json={}, headers=super_auth_headers)
    await client.patch(
        "/api/v1/agents/arch-sentinel/status",
        json={"status": "Available", "reason": "Ready for Bengali test"},
        headers=super_auth_headers,
    )

    submit_res = await client.post(
        "/api/v1/executions",
        json={
            "agent_slug": "arch-sentinel",
            "instruction": "inspect backend/app/main.py",
            "scope": "read_only",
            "context": {"path": "backend/app/main.py", "language": "bn"},
        },
        headers=auth_headers,
    )
    assert submit_res.status_code == 202
    execution_id = submit_res.json()["execution_id"]

    res_data = {}
    for _ in range(30):
        get_res = await client.get(f"/api/v1/executions/{execution_id}", headers=auth_headers)
        assert get_res.status_code == 200
        res_data = get_res.json()
        if res_data["status"] != "Pending":
            break
        await asyncio.sleep(0.1)

    assert res_data["status"] == "Completed"
    assert res_data["bn_report"] is not None
    assert res_data["bn_report"]["agent_name_bn"] == "কোডিং সহকারী"
    assert "বিশ্লেষণ সম্পন্ন" in res_data["bn_report"]["summary_bn"]
    # English output stays intact while carrying additive bn_report when language=bn
    parsed = json.loads(res_data["output"])
    assert parsed.get("file") == "backend/app/main.py"
    assert "bn_report" in parsed
