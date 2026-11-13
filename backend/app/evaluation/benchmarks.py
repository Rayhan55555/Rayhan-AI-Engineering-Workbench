from typing import Dict, List

BENCHMARK_TASKS: List[Dict[str, str]] = [
    {
        "id": "bench-code-ast",
        "agent": "arch-sentinel",
        "instruction": "analyze backend/app/main.py and identify architectural issues",
        "expected_section": "Findings",
    },
    {
        "id": "bench-sec-sql",
        "agent": "security-agent",
        "instruction": "suggest fixes for INJ-001 SQL injection risk",
        "expected_section": "Remediation",
    },
    {
        "id": "bench-test-gap",
        "agent": "testing-agent",
        "instruction": "find test gaps in backend/app/routers/auth.py",
        "expected_section": "Gaps",
    },
]
