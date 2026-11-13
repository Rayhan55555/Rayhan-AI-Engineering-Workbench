import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import PROJECT_ROOT
from backend.app.tools.base_tool import BaseTool, ToolResult


class DependencyFinding(BaseModel):
    ecosystem: str  # 'python' or 'npm'
    package: str
    current_version: str
    issue: str
    severity: str
    recommendation: str


# Offline pattern list of packages with known CVEs or major deprecations
KNOWN_VULNERABLE_PATTERNS = [
    {
        "ecosystem": "python",
        "package": "fastapi",
        "pattern": r"fastapi\s*(?:==|<=|<)\s*0\.(?:[0-8]\d|9[0-4])\b",
        "issue": "FastAPI < 0.95.0 has known ReDoS / Swagger UI vulnerabilities",
        "severity": "Medium",
        "recommendation": "Upgrade fastapi to >= 0.100.0",
    },
    {
        "ecosystem": "python",
        "package": "pydantic",
        "pattern": r"pydantic\s*(?:==|<=|<)\s*1\.",
        "issue": "Pydantic v1 is deprecated and lacks modern security validations",
        "severity": "Low",
        "recommendation": "Migrate to Pydantic v2 (>= 2.5.0)",
    },
    {
        "ecosystem": "python",
        "package": "cryptography",
        "pattern": r"cryptography\s*(?:==|<=|<)\s*(?:[0-3]\d|40)\.",
        "issue": "Cryptography < 41.0.0 has known OpenSSL vulnerability CVE-2023-38325",
        "severity": "High",
        "recommendation": "Upgrade cryptography to >= 41.0.0",
    },
    {
        "ecosystem": "python",
        "package": "urllib3",
        "pattern": r"urllib3\s*(?:==|<=|<)\s*(?:1\.2[0-5]|1\.1\d)\.",
        "issue": "Urllib3 < 1.26.5 susceptible to CRLF injection in HTTP headers",
        "severity": "High",
        "recommendation": "Upgrade urllib3 to >= 1.26.18 or 2.0.7",
    },
    {
        "ecosystem": "python",
        "package": "requests",
        "pattern": r"requests\s*(?:==|<=|<)\s*2\.(?:[0-2]\d|30)\b",
        "issue": "Requests < 2.31.0 leaks Proxy-Authorization headers on redirect",
        "severity": "Medium",
        "recommendation": "Upgrade requests to >= 2.31.0",
    },
    {
        "ecosystem": "npm",
        "package": "axios",
        "pattern": r"0\.(?:[0-9]|1[0-9]|2[0-1])\.",
        "issue": "Axios < 0.21.1 susceptible to SSRF and prototype pollution",
        "severity": "High",
        "recommendation": "Upgrade axios to >= 1.6.0",
    },
    {
        "ecosystem": "npm",
        "package": "lodash",
        "pattern": r"4\.17\.(?:[0-9]|1[0-9]|20)\b",
        "issue": "Lodash <= 4.17.20 prototype pollution vulnerabilities (CVE-2021-23337)",
        "severity": "High",
        "recommendation": "Upgrade lodash to >= 4.17.21",
    },
    {
        "ecosystem": "npm",
        "package": "express",
        "pattern": r"4\.(?:[0-9]|1[0-5])\.",
        "issue": "Express < 4.16.0 contains qs query parser vulnerability",
        "severity": "Medium",
        "recommendation": "Upgrade express to >= 4.18.0",
    },
]


class DependencyAuditorTool(BaseTool):
    name = "dependency_auditor"
    description = (
        "Offline pattern-based vulnerability auditor for requirements.txt and package.json. "
        "Checks known vulnerable version ranges, unpinned dependencies, and deprecations without external API calls."
    )
    required_permission = PermissionLevel.READ_ONLY
    safe_by_default = True

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        findings: List[DependencyFinding] = []
        evidence: List[str] = []

        # 1. Audit Python requirements.txt
        req_file = PROJECT_ROOT / "backend" / "requirements.txt"
        if req_file.exists():
            py_findings = self.audit_python_requirements(req_file.read_text(encoding="utf-8"))
            findings.extend(py_findings)
            evidence.append(f"Audited backend/requirements.txt: {len(py_findings)} dependency risks detected")

        # 2. Audit Node.js package.json
        pkg_file = PROJECT_ROOT / "package.json"
        if pkg_file.exists():
            npm_findings = self.audit_package_json(pkg_file.read_text(encoding="utf-8"))
            findings.extend(npm_findings)
            evidence.append(f"Audited package.json: {len(npm_findings)} dependency risks detected")

        summary = {
            "total_dependency_findings": len(findings),
            "findings": [f.model_dump() for f in findings],
        }

        return ToolResult(
            success=True,
            output=summary,
            evidence=evidence,
            simulated=False,
            metadata={"findings_count": len(findings)},
        )

    def audit_python_requirements(self, text: str) -> List[DependencyFinding]:
        findings: List[DependencyFinding] = []
        for line in text.splitlines():
            clean = line.strip()
            if not clean or clean.startswith("#"):
                continue

            # Check known vulnerable patterns
            for pat in KNOWN_VULNERABLE_PATTERNS:
                if pat["ecosystem"] == "python" and pat["package"] in clean.lower():
                    if re.search(pat["pattern"], clean, re.IGNORECASE):
                        findings.append(
                            DependencyFinding(
                                ecosystem="python",
                                package=pat["package"],
                                current_version=clean,
                                issue=pat["issue"],
                                severity=pat["severity"],
                                recommendation=pat["recommendation"],
                            )
                        )

            # Check unpinned versions (bare package name)
            if not any(op in clean for op in ("==", ">=", "<=", "~=", "^", ">", "<")):
                findings.append(
                    DependencyFinding(
                        ecosystem="python",
                        package=clean,
                        current_version="unpinned",
                        issue="Unpinned package version allows unexpected major upgrades",
                        severity="Low",
                        recommendation=f"Pin specific version: {clean}==x.y.z",
                    )
                )

        return findings

    def audit_package_json(self, text: str) -> List[DependencyFinding]:
        findings: List[DependencyFinding] = []
        try:
            data = json.loads(text)
        except Exception:
            return findings

        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

        for pkg, ver in deps.items():
            for pat in KNOWN_VULNERABLE_PATTERNS:
                if pat["ecosystem"] == "npm" and pat["package"] == pkg:
                    if re.search(pat["pattern"], ver):
                        findings.append(
                            DependencyFinding(
                                ecosystem="npm",
                                package=pkg,
                                current_version=ver,
                                issue=pat["issue"],
                                severity=pat["severity"],
                                recommendation=pat["recommendation"],
                            )
                        )

        # Check missing package-lock.json
        lock_file = PROJECT_ROOT / "package-lock.json"
        if not lock_file.exists():
            findings.append(
                DependencyFinding(
                    ecosystem="npm",
                    package="repository",
                    current_version="none",
                    issue="Missing package-lock.json or lockfile",
                    severity="Low",
                    recommendation="Run 'npm install' or commit package-lock.json to ensure deterministic builds.",
                )
            )

        return findings
