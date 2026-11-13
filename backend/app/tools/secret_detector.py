import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import (
    PROJECT_ROOT,
    SandboxSecurityError,
    resolve_safe_path,
)
from backend.app.security.patterns import (
    AWS_KEY_PATTERN,
    BEARER_TOKEN_PATTERN,
    DATABASE_URL_CREDENTIALS,
    GENERIC_API_KEY_PATTERN,
    JWT_SECRET_PATTERN,
    PASSWORD_ASSIGNMENT_PATTERN,
    PRIVATE_KEY_HEADER,
)
from backend.app.tools.base_tool import BaseTool, ToolResult


class SecretFinding(BaseModel):
    rule_id: str = "AUTH-001"
    severity: str = "Critical"
    pattern_type: str
    file: str
    line: int
    masked_preview: str
    title: str
    fix_guidance: str
    cwe_id: str = "CWE-798"


def mask_secret(raw_value: str) -> str:
    """
    Masks sensitive values so raw credentials are NEVER exposed.
    Returns: first 4 characters + '****' (or '****' if too short).
    """
    clean = raw_value.strip().strip("'\"")
    if len(clean) <= 4:
        return "****"
    return f"{clean[:4]}****"


class SecretDetectorTool(BaseTool):
    name = "secret_detector"
    description = (
        "Scans files for hardcoded secrets, API tokens, AWS keys, passwords, "
        "and database credentials. Strictly outputs masked previews only."
    )
    required_permission = PermissionLevel.READ_ONLY
    safe_by_default = True

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        target_path_str = params.get("path") or params.get("file_path")
        code_content = params.get("content")

        findings: List[SecretFinding] = []

        if code_content is not None:
            findings = self.scan_content(code_content, file_label="in-memory buffer")
        elif target_path_str:
            try:
                safe_path = resolve_safe_path(target_path_str, PROJECT_ROOT)
                # Ignore .env.example
                if safe_path.name == ".env.example":
                    return ToolResult(
                        success=True,
                        output={"total_secrets": 0, "findings": []},
                        evidence=[f"Excluded .env.example template from secret detection"],
                        simulated=False,
                    )
                if safe_path.is_file():
                    content = safe_path.read_text(encoding="utf-8", errors="replace")
                    rel_path = str(safe_path.relative_to(PROJECT_ROOT))
                    findings = self.scan_content(content, file_label=rel_path)
                elif safe_path.is_dir():
                    findings = self.scan_directory(safe_path)
            except SandboxSecurityError as e:
                return ToolResult(
                    success=False,
                    output={"total_secrets": 0, "findings": []},
                    error=str(e),
                    evidence=[f"Blocked path: {target_path_str}"],
                    simulated=False,
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    output={"total_secrets": 0, "findings": []},
                    error=f"Error reading file for secrets: {str(e)}",
                    evidence=[],
                    simulated=False,
                )
        else:
            # Default to full workspace scan
            findings = self.scan_directory(PROJECT_ROOT)

        findings_data = [f.model_dump() for f in findings]
        return ToolResult(
            success=True,
            output={
                "total_secrets": len(findings),
                "findings": findings_data,
            },
            evidence=[
                f"Secret detection complete: {len(findings)} hardcoded secret patterns found",
                "All secret values strictly masked (e.g. sk-a****)",
            ],
            simulated=False,
            metadata={"secrets_detected": len(findings)},
        )

    def scan_content(self, content: str, file_label: str) -> List[SecretFinding]:
        findings: List[SecretFinding] = []
        lines = content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                # Skip pure comments
                continue

            # 1. AWS Key
            aws_match = AWS_KEY_PATTERN.search(stripped)
            if aws_match:
                findings.append(
                    SecretFinding(
                        rule_id="AUTH-001",
                        severity="Critical",
                        pattern_type="aws_access_key",
                        file=file_label,
                        line=line_num,
                        masked_preview=mask_secret(aws_match.group(1)),
                        title="Hardcoded AWS Access Key ID Detected",
                        fix_guidance="Store AWS keys in environment variables or IAM roles.",
                    )
                )

            # 2. Generic API Key
            api_match = GENERIC_API_KEY_PATTERN.search(stripped)
            if api_match:
                raw_key = api_match.group(1)
                if not raw_key.lower().startswith("my_") and "example" not in raw_key.lower():
                    findings.append(
                        SecretFinding(
                            rule_id="AUTH-001",
                            severity="Critical",
                            pattern_type="api_key",
                            file=file_label,
                            line=line_num,
                            masked_preview=mask_secret(raw_key),
                            title="Hardcoded API Secret Detected",
                            fix_guidance="Load API keys from process.env or settings.py.",
                        )
                    )

            # 3. Hardcoded JWT Secret
            jwt_match = JWT_SECRET_PATTERN.search(stripped)
            if jwt_match:
                raw_secret = jwt_match.group(1)
                if not raw_secret.lower().startswith("my_") and "example" not in raw_secret.lower():
                    findings.append(
                        SecretFinding(
                            rule_id="AUTH-004",
                            severity="High",
                            pattern_type="jwt_secret",
                            file=file_label,
                            line=line_num,
                            masked_preview=mask_secret(raw_secret),
                            title="Hardcoded JWT Secret Detected",
                            fix_guidance="Move JWT secret to settings.SECRET_KEY environment variable.",
                        )
                    )

            # 4. Hardcoded Password
            pwd_match = PASSWORD_ASSIGNMENT_PATTERN.search(stripped)
            if pwd_match:
                raw_pwd = pwd_match.group(1)
                if not raw_pwd.lower().startswith("my_") and "example" not in raw_pwd.lower() and "dummy" not in raw_pwd.lower():
                    findings.append(
                        SecretFinding(
                            rule_id="AUTH-002",
                            severity="High",
                            pattern_type="password",
                            file=file_label,
                            line=line_num,
                            masked_preview=mask_secret(raw_pwd),
                            title="Hardcoded Password Detected",
                            fix_guidance="Never commit passwords in source code; use bcrypt hashing and input prompts.",
                        )
                    )

            # 5. Database URL with credentials
            db_match = DATABASE_URL_CREDENTIALS.search(stripped)
            if db_match:
                raw_cred = db_match.group(1)
                findings.append(
                    SecretFinding(
                        rule_id="AUTH-001",
                        severity="Critical",
                        pattern_type="database_credentials",
                        file=file_label,
                        line=line_num,
                        masked_preview=mask_secret(raw_cred),
                        title="Database Credentials in Connection String",
                        fix_guidance="Parameterize database credentials using DATABASE_URL environment variable.",
                    )
                )

            # 6. Private Key Header
            if PRIVATE_KEY_HEADER.search(stripped):
                findings.append(
                    SecretFinding(
                        rule_id="DATA-003",
                        severity="Critical",
                        pattern_type="private_key",
                        file=file_label,
                        line=line_num,
                        masked_preview="-----BEGIN PRIV****",
                        title="Private Key Block Header Detected",
                        fix_guidance="Remove private key files from git tracking immediately and rotate certificates.",
                    )
                )

            # 7. Bearer Token
            bearer_match = BEARER_TOKEN_PATTERN.search(stripped)
            if bearer_match:
                raw_token = bearer_match.group(1)
                if len(raw_token) > 15 and "example" not in raw_token.lower():
                    findings.append(
                        SecretFinding(
                            rule_id="AUTH-001",
                            severity="High",
                            pattern_type="bearer_token",
                            file=file_label,
                            line=line_num,
                            masked_preview=mask_secret(raw_token),
                            title="Hardcoded Bearer Token Detected",
                            fix_guidance="Provide authorization tokens via request headers dynamically.",
                        )
                    )

        return findings

    def scan_directory(self, dir_path: Path) -> List[SecretFinding]:
        findings: List[SecretFinding] = []
        skip_dirs = {"node_modules", ".git", "__pycache__", "dist", "build", ".pytest_cache", "venv"}

        for path in dir_path.rglob("*"):
            if not path.is_file():
                continue
            if any(part in skip_dirs for part in path.parts):
                continue
            if path.name == ".env.example":
                continue
            if path.suffix.lower() not in (".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".toml", ".txt", ".sql"):
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                rel_path = str(path.relative_to(PROJECT_ROOT))
                findings.extend(self.scan_content(content, file_label=rel_path))
            except Exception:
                continue

        return findings
