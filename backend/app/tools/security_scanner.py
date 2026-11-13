import ast
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import (
    MAX_FILE_SIZE_BYTES,
    PROJECT_ROOT,
    SandboxSecurityError,
    resolve_safe_path,
)
from backend.app.security.patterns import (
    COMMAND_INJECTION_SHELL,
    INSECURE_RANDOM,
    INSECURE_YAML_LOAD,
    JWT_ALG_NONE_PATTERN,
    LOGGING_SENSITIVE_DATA,
    PATH_TRAVERSAL_CONCAT,
    SQL_INJECTION_FORMAT,
    STACK_TRACE_IN_RESPONSE,
    TEMPLATE_INJECTION_EVAL,
    WEAK_HASHING_ALGORITHM,
)
from backend.app.security.rules import RULE_CATALOG, SecurityRule
from backend.app.tools.base_tool import BaseTool, ToolResult
from backend.app.tools.secret_detector import SecretDetectorTool


class SecurityFinding(BaseModel):
    rule_id: str
    severity: str
    file: str
    line: int
    title: str
    snippet: str = Field(..., max_length=100)
    fix: str
    cwe: str


class SecurityScannerTool(BaseTool):
    name = "security_scanner"
    description = (
        "Performs offline static code analysis across Python and TypeScript files using "
        "Python AST visitors and custom rule regexes. Identifies injection, auth, data leakage, "
        "and validation flaws with line numbers and remediation guidance."
    )
    required_permission = PermissionLevel.READ_ONLY
    safe_by_default = True

    def __init__(self):
        self.secret_detector = SecretDetectorTool()

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        target_path_str = params.get("path") or params.get("file_path")
        code_content = params.get("content")

        start_time = time.perf_counter()
        findings: List[SecurityFinding] = []
        scanned_files_count = 0

        if code_content is not None:
            findings = self.scan_file_content(code_content, file_label="in-memory buffer")
            scanned_files_count = 1
        elif target_path_str:
            try:
                safe_path = resolve_safe_path(target_path_str, PROJECT_ROOT)
                if safe_path.is_file():
                    findings = self.scan_file(safe_path)
                    scanned_files_count = 1
                elif safe_path.is_dir():
                    res = self.scan_project(safe_path)
                    findings = res["findings"]
                    scanned_files_count = res["scanned_files"]
            except SandboxSecurityError as e:
                return ToolResult(
                    success=False,
                    output={},
                    error=str(e),
                    evidence=[f"Blocked scanner path: {target_path_str}"],
                    simulated=False,
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    output={},
                    error=f"Error scanning path: {str(e)}",
                    evidence=[],
                    simulated=False,
                )
        else:
            # Full workspace project scan
            res = self.scan_project(PROJECT_ROOT)
            findings = res["findings"]
            scanned_files_count = res["scanned_files"]

        duration_ms = int((time.perf_counter() - start_time) * 1000)

        # Aggregate counts by severity
        by_severity = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }
        for f in findings:
            sev_key = f.severity.lower()
            if sev_key in by_severity:
                by_severity[sev_key] += 1

        summary = {
            "scanned_files": scanned_files_count,
            "total_findings": len(findings),
            "by_severity": by_severity,
            "findings": [f.model_dump() for f in findings],
            "scan_duration_ms": duration_ms,
        }

        return ToolResult(
            success=True,
            output=summary,
            evidence=[
                f"Scanned {scanned_files_count} files across project workspace",
                f"Applied 18 static security analysis rules",
                f"Total findings detected: {len(findings)} (Critical: {by_severity['critical']}, High: {by_severity['high']})",
            ],
            simulated=False,
            metadata=summary,
        )

    def scan_file(self, path: Path) -> List[SecurityFinding]:
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return []
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            rel_path = str(path.relative_to(PROJECT_ROOT))
            return self.scan_file_content(content, file_label=rel_path)
        except Exception:
            return []

    def scan_file_content(self, content: str, file_label: str) -> List[SecurityFinding]:
        findings: List[SecurityFinding] = []
        is_python = file_label.endswith(".py") or ("def " in content and "import " in content)

        # 1. AST Checks for Python
        if is_python:
            findings.extend(self._scan_python_ast(content, file_label))

        # 2. Regex Rule Checks for both Python & TypeScript
        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#") or trimmed.startswith("//"):
                continue

            # INJ-001: SQL Injection
            if SQL_INJECTION_FORMAT.search(trimmed):
                rule = RULE_CATALOG["INJ-001"]
                findings.append(
                    SecurityFinding(
                        rule_id=rule.id,
                        severity=rule.severity.value,
                        file=file_label,
                        line=idx,
                        title=rule.title,
                        snippet=trimmed[:100],
                        fix=rule.fix_guidance,
                        cwe=rule.cwe_id,
                    )
                )

            # INJ-002: Command Injection
            if COMMAND_INJECTION_SHELL.search(trimmed):
                rule = RULE_CATALOG["INJ-002"]
                findings.append(
                    SecurityFinding(
                        rule_id=rule.id,
                        severity=rule.severity.value,
                        file=file_label,
                        line=idx,
                        title=rule.title,
                        snippet=trimmed[:100],
                        fix=rule.fix_guidance,
                        cwe=rule.cwe_id,
                    )
                )

            # INJ-003: Path Traversal
            if PATH_TRAVERSAL_CONCAT.search(trimmed):
                rule = RULE_CATALOG["INJ-003"]
                findings.append(
                    SecurityFinding(
                        rule_id=rule.id,
                        severity=rule.severity.value,
                        file=file_label,
                        line=idx,
                        title=rule.title,
                        snippet=trimmed[:100],
                        fix=rule.fix_guidance,
                        cwe=rule.cwe_id,
                    )
                )

            # INJ-004: eval / exec
            if TEMPLATE_INJECTION_EVAL.search(trimmed):
                rule = RULE_CATALOG["INJ-004"]
                findings.append(
                    SecurityFinding(
                        rule_id=rule.id,
                        severity=rule.severity.value,
                        file=file_label,
                        line=idx,
                        title=rule.title,
                        snippet=trimmed[:100],
                        fix=rule.fix_guidance,
                        cwe=rule.cwe_id,
                    )
                )

            # AUTH-003: JWT alg none
            if JWT_ALG_NONE_PATTERN.search(trimmed):
                rule = RULE_CATALOG["AUTH-003"]
                findings.append(
                    SecurityFinding(
                        rule_id=rule.id,
                        severity=rule.severity.value,
                        file=file_label,
                        line=idx,
                        title=rule.title,
                        snippet=trimmed[:100],
                        fix=rule.fix_guidance,
                        cwe=rule.cwe_id,
                    )
                )

            # DATA-001: Sensitive data logged
            if LOGGING_SENSITIVE_DATA.search(trimmed):
                rule = RULE_CATALOG["DATA-001"]
                findings.append(
                    SecurityFinding(
                        rule_id=rule.id,
                        severity=rule.severity.value,
                        file=file_label,
                        line=idx,
                        title=rule.title,
                        snippet=trimmed[:100],
                        fix=rule.fix_guidance,
                        cwe=rule.cwe_id,
                    )
                )

            # DATA-002: Stack trace returned
            if STACK_TRACE_IN_RESPONSE.search(trimmed):
                rule = RULE_CATALOG["DATA-002"]
                findings.append(
                    SecurityFinding(
                        rule_id=rule.id,
                        severity=rule.severity.value,
                        file=file_label,
                        line=idx,
                        title=rule.title,
                        snippet=trimmed[:100],
                        fix=rule.fix_guidance,
                        cwe=rule.cwe_id,
                    )
                )

            # INP-001: Weak hashing
            if WEAK_HASHING_ALGORITHM.search(trimmed):
                rule = RULE_CATALOG["INP-001"]
                findings.append(
                    SecurityFinding(
                        rule_id=rule.id,
                        severity=rule.severity.value,
                        file=file_label,
                        line=idx,
                        title=rule.title,
                        snippet=trimmed[:100],
                        fix=rule.fix_guidance,
                        cwe=rule.cwe_id,
                    )
                )

            # INP-002: Insecure random
            if INSECURE_RANDOM.search(trimmed):
                rule = RULE_CATALOG["INP-002"]
                findings.append(
                    SecurityFinding(
                        rule_id=rule.id,
                        severity=rule.severity.value,
                        file=file_label,
                        line=idx,
                        title=rule.title,
                        snippet=trimmed[:100],
                        fix=rule.fix_guidance,
                        cwe=rule.cwe_id,
                    )
                )

            # INP-003: Insecure YAML load
            if INSECURE_YAML_LOAD.search(trimmed):
                rule = RULE_CATALOG["INP-003"]
                findings.append(
                    SecurityFinding(
                        rule_id=rule.id,
                        severity=rule.severity.value,
                        file=file_label,
                        line=idx,
                        title=rule.title,
                        snippet=trimmed[:100],
                        fix=rule.fix_guidance,
                        cwe=rule.cwe_id,
                    )
                )

        # 3. Add Secret Detector Findings (masked)
        secret_findings = self.secret_detector.scan_content(content, file_label)
        for sf in secret_findings:
            findings.append(
                SecurityFinding(
                    rule_id=sf.rule_id,
                    severity=sf.severity,
                    file=sf.file,
                    line=sf.line,
                    title=sf.title,
                    snippet=f"Detected pattern: {sf.pattern_type} [{sf.masked_preview}]"[:100],
                    fix=sf.fix_guidance,
                    cwe=sf.cwe_id,
                )
            )

        return findings

    def _scan_python_ast(self, content: str, file_label: str) -> List[SecurityFinding]:
        findings: List[SecurityFinding] = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return findings

        for node in ast.walk(tree):
            # Check for shell=True in Call nodes
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id

                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        rule = RULE_CATALOG["INJ-002"]
                        findings.append(
                            SecurityFinding(
                                rule_id=rule.id,
                                severity=rule.severity.value,
                                file=file_label,
                                line=node.lineno,
                                title=rule.title,
                                snippet=f"{func_name}(..., shell=True)"[:100],
                                fix=rule.fix_guidance,
                                cwe=rule.cwe_id,
                            )
                        )

        return findings

    def scan_project(self, root_dir: Path) -> Dict[str, Any]:
        all_findings: List[SecurityFinding] = []
        scanned_count = 0
        skip_dirs = {"node_modules", ".git", "__pycache__", "dist", "build", ".pytest_cache", "venv"}

        for path in root_dir.rglob("*"):
            if not path.is_file():
                continue
            if any(part in skip_dirs for part in path.parts):
                continue
            if path.name == ".env.example":
                continue
            if path.suffix.lower() not in (".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".toml", ".sql"):
                continue

            findings = self.scan_file(path)
            all_findings.extend(findings)
            scanned_count += 1

        return {
            "scanned_files": scanned_count,
            "findings": all_findings,
        }
