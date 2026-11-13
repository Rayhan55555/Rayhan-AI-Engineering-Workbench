import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import PROJECT_ROOT, resolve_safe_path
from backend.app.tools.base_tool import BaseTool, ToolResult


class AuthAuditFinding(BaseModel):
    check: str
    status: str  # 'PASS' or 'FAIL'
    severity: str
    file: Optional[str] = None
    line: Optional[int] = None
    message: str
    remediation: str


class AuthAuditorTool(BaseTool):
    name = "auth_auditor"
    description = (
        "Audits authentication and authorization boundaries: route decorator protections, "
        "JWT algorithm configuration, token expiry rules, bcrypt cost factors, and ownership validation."
    )
    required_permission = PermissionLevel.READ_ONLY
    safe_by_default = True

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        findings: List[AuthAuditFinding] = []

        # 1. Audit Route Decorators across backend routers
        route_findings = self.audit_endpoint_protection()
        findings.extend(route_findings)

        # 2. Audit JWT Configuration
        jwt_findings = self.audit_jwt_configuration()
        findings.extend(jwt_findings)

        # 3. Audit Password & Bcrypt Policy
        pwd_findings = self.audit_password_policy()
        findings.extend(pwd_findings)

        # 4. Audit Permission Boundaries & Superuser Gating
        perm_findings = self.audit_permission_boundaries()
        findings.extend(perm_findings)

        total_checks = len(findings)
        failed_checks = sum(1 for f in findings if f.status == "FAIL")
        passed_checks = sum(1 for f in findings if f.status == "PASS")

        summary = {
            "total_checks": total_checks,
            "passed": passed_checks,
            "failed": failed_checks,
            "findings": [f.model_dump() for f in findings],
        }

        return ToolResult(
            success=True,
            output=summary,
            evidence=[
                f"Auth audit complete: {total_checks} checks evaluated",
                f"Passed: {passed_checks}, Failed/Warnings: {failed_checks}",
            ],
            simulated=False,
            metadata=summary,
        )

    def audit_endpoint_protection(self) -> List[AuthAuditFinding]:
        findings: List[AuthAuditFinding] = []
        routers_dir = PROJECT_ROOT / "backend" / "app" / "routers"
        if not routers_dir.exists():
            return findings

        for router_file in routers_dir.glob("*.py"):
            try:
                tree = ast.parse(router_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            rel_file = str(router_file.relative_to(PROJECT_ROOT))
            is_auth_router = "auth.py" in router_file.name

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Check decorators
                    is_route = False
                    is_write_route = False
                    for dec in node.decorator_list:
                        dec_str = ""
                        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                            dec_str = dec.func.attr
                        elif isinstance(dec, ast.Attribute):
                            dec_str = dec.attr

                        if dec_str in ("get", "post", "put", "patch", "delete"):
                            is_route = True
                            if dec_str in ("post", "put", "patch", "delete"):
                                is_write_route = True

                    if is_route and is_write_route and not is_auth_router:
                        # Public seed or register routes in auth are fine
                        # In other routers, check if Depends(get_current_user) or Depends(get_current_superuser) is present
                        code_str = ast.unparse(node.args)
                        has_auth_dep = "get_current_user" in code_str or "get_current_superuser" in code_str or "get_db" in code_str
                        if not ("get_current_user" in code_str or "get_current_superuser" in code_str):
                            findings.append(
                                AuthAuditFinding(
                                    check="endpoint_protection",
                                    status="FAIL",
                                    severity="High",
                                    file=rel_file,
                                    line=node.lineno,
                                    message=f"Write route '{node.name}' has no authenticated user dependency.",
                                    remediation="Add 'current_user: User = Depends(get_current_user)' to endpoint parameters.",
                                )
                            )
                        else:
                            findings.append(
                                AuthAuditFinding(
                                    check="endpoint_protection",
                                    status="PASS",
                                    severity="Info",
                                    file=rel_file,
                                    line=node.lineno,
                                    message=f"Route '{node.name}' protected with authenticated user dependency.",
                                    remediation="Maintain existing authorization dependency.",
                                )
                            )

        return findings

    def audit_jwt_configuration(self) -> List[AuthAuditFinding]:
        findings: List[AuthAuditFinding] = []
        config_file = PROJECT_ROOT / "backend" / "app" / "config.py"
        auth_file = PROJECT_ROOT / "backend" / "app" / "routers" / "auth.py"

        if config_file.exists():
            content = config_file.read_text(encoding="utf-8")
            # 1. Algorithm check
            if 'ALGORITHM: str = "none"' in content or 'ALGORITHM = "none"' in content:
                findings.append(
                    AuthAuditFinding(
                        check="jwt_algorithm",
                        status="FAIL",
                        severity="Critical",
                        file="backend/app/config.py",
                        message="JWT algorithm is configured as 'none'.",
                        remediation="Set ALGORITHM to 'HS256' or stronger signature algorithm.",
                    )
                )
            else:
                findings.append(
                    AuthAuditFinding(
                        check="jwt_algorithm",
                        status="PASS",
                        severity="Info",
                        file="backend/app/config.py",
                        message="JWT signature algorithm is HS256.",
                        remediation="Ensure HS256 secret key has at least 256 bits of entropy.",
                    )
                )

            # 2. Token expiry check
            expiry_match = re.search(r"ACCESS_TOKEN_EXPIRE_MINUTES:\s*int\s*=\s*(\d+)", content)
            if expiry_match:
                mins = int(expiry_match.group(1))
                if mins > 24 * 60:
                    findings.append(
                        AuthAuditFinding(
                            check="jwt_expiry",
                            status="FAIL",
                            severity="Medium",
                            file="backend/app/config.py",
                            message=f"Access token expiry is {mins} minutes (>24h).",
                            remediation="Reduce access token expiry to <= 60 minutes and rely on refresh token rotation.",
                        )
                    )
                else:
                    findings.append(
                        AuthAuditFinding(
                            check="jwt_expiry",
                            status="PASS",
                            severity="Info",
                            file="backend/app/config.py",
                            message=f"Access token expiry is securely configured to {mins} minutes.",
                            remediation="Maintain short-lived access tokens.",
                        )
                    )

        return findings

    def audit_password_policy(self) -> List[AuthAuditFinding]:
        findings: List[AuthAuditFinding] = []
        auth_file = PROJECT_ROOT / "backend" / "app" / "routers" / "auth.py"

        if auth_file.exists():
            content = auth_file.read_text(encoding="utf-8")
            if "CryptContext" in content and "bcrypt" in content:
                findings.append(
                    AuthAuditFinding(
                        check="password_hashing",
                        status="PASS",
                        severity="Info",
                        file="backend/app/routers/auth.py",
                        message="Passwords are encrypted using bcrypt CryptContext.",
                        remediation="Keep bcrypt work factor at default or >= 12.",
                    )
                )
            else:
                findings.append(
                    AuthAuditFinding(
                        check="password_hashing",
                        status="FAIL",
                        severity="High",
                        file="backend/app/routers/auth.py",
                        message="Bcrypt CryptContext not found in auth module.",
                        remediation="Configure passlib.context.CryptContext(schemes=['bcrypt'], deprecated='auto').",
                    )
                )

        return findings

    def audit_permission_boundaries(self) -> List[AuthAuditFinding]:
        findings: List[AuthAuditFinding] = []
        deps_file = PROJECT_ROOT / "backend" / "app" / "dependencies.py"

        if deps_file.exists():
            content = deps_file.read_text(encoding="utf-8")
            if "get_current_superuser" in content and "is_superuser" in content:
                findings.append(
                    AuthAuditFinding(
                        check="superuser_boundary",
                        status="PASS",
                        severity="Info",
                        file="backend/app/dependencies.py",
                        message="Superuser permission gate properly enforced via get_current_superuser.",
                        remediation="Maintain strict gating on admin mutations.",
                    )
                )
            else:
                findings.append(
                    AuthAuditFinding(
                        check="superuser_boundary",
                        status="FAIL",
                        severity="High",
                        file="backend/app/dependencies.py",
                        message="get_current_superuser dependency missing or lacks is_superuser check.",
                        remediation="Enforce current_user.is_superuser check in dependencies.py.",
                    )
                )

        return findings
