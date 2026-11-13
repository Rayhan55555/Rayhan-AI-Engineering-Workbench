from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional
from backend.app.agents.base_agent import (
    AgentResult,
    AgentTask,
    Artifact,
    BaseAgent,
    CapabilityDescription,
    Evidence,
    ExecutionContext,
    TaskScope,
    ValidationResult,
)
from backend.app.security.rules import RULE_CATALOG, SECURITY_RULES
from backend.app.tools.auth_auditor import AuthAuditorTool
from backend.app.tools.dependency_auditor import DependencyAuditorTool
from backend.app.tools.secret_detector import SecretDetectorTool
from backend.app.tools.security_scanner import SecurityScannerTool


class SecurityAgent(BaseAgent):
    """
    Phase 05 Full Implementation of the Security Hardening Agent.
    Performs comprehensive offline static security analysis, secret detection,
    auth & authorization auditing, and dependency vulnerability pattern checking.
    
    Safety Guardrail:
    - IMPLEMENT scope is strictly locked (manual security review required).
    - Secret values are strictly masked in all findings and reports.
    """
    slug = "security-agent"
    name = "Security Hardening Agent"
    purpose = (
        "Static code analysis, credential leakage auditing, JWT/auth boundary verification, "
        "and offline dependency vulnerability detection."
    )
    phase = 5
    version = "1.0.0"
    allowed_tools = [
        "security_scanner",
        "secret_detector",
        "auth_auditor",
        "dependency_auditor",
    ]
    required_permissions = ["READ_ONLY", "SUGGEST"]
    limitations = [
        "Pattern-based only — may have false positives",
        "No live CVE database — offline patterns only",
        "Cannot detect runtime security issues or dynamic exploits",
        "IMPLEMENT scope locked — manual security fixes required by engineer",
    ]

    def __init__(self):
        self.security_scanner = SecurityScannerTool()
        self.secret_detector = SecretDetectorTool()
        self.auth_auditor = AuthAuditorTool()
        self.dependency_auditor = DependencyAuditorTool()

    async def validate_input(self, task: AgentTask) -> ValidationResult:
        instruction = task.instruction.strip()
        if len(instruction) < 3:
            return ValidationResult(
                valid=False,
                error="Instruction is too short (minimum 3 characters required).",
            )
        if len(instruction) > 2000:
            return ValidationResult(
                valid=False,
                error="Instruction exceeds maximum length of 2,000 characters.",
            )

        # Security Agent IMPLEMENT scope is permanently locked
        if task.scope == TaskScope.implement:
            return ValidationResult(
                valid=False,
                error=(
                    "Security fixes must be reviewed and applied manually. "
                    "This protects against automated security changes that could introduce new vulnerabilities. "
                    "Use SUGGEST scope for remediation guidance."
                ),
            )

        if task.scope == TaskScope.deploy:
            return ValidationResult(
                valid=False,
                error="Scope 'deploy' is locked until Phase 11.",
            )

        return ValidationResult(valid=True)

    async def execute(self, task: AgentTask, context: ExecutionContext) -> AgentResult:
        instruction = task.instruction.strip().lower()
        scope = task.scope

        # Extract target path if specified
        target_path: Optional[str] = task.context.get("path") or task.context.get("file_path")
        if not target_path:
            path_matches = re.findall(r"[\w\./\-]+\.(?:py|ts|tsx|js|json|md|txt|sql)", task.instruction)
            if path_matches:
                target_path = path_matches[0]

        evidence_items: List[Evidence] = []
        artifacts: List[Artifact] = []

        # -------------------------------------------------------------
        # SUGGEST Scope: Suggest detailed remediation guidance for findings
        # -------------------------------------------------------------
        if scope == TaskScope.suggest or "suggest" in instruction or "fix" in instruction:
            # Check if specific finding_id requested (e.g. INJ-001, AUTH-001)
            finding_id_match = re.search(r"\b([A-Z]{3,4}-\d{3})\b", task.instruction.upper())
            target_rule_id = finding_id_match.group(1) if finding_id_match else None

            recommendations = []
            if target_rule_id and target_rule_id in RULE_CATALOG:
                rule = RULE_CATALOG[target_rule_id]
                recommendations.append({
                    "priority": 1,
                    "finding_id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity.value,
                    "cwe": rule.cwe_id,
                    "remediation": rule.fix_guidance,
                    "effort": "low" if rule.severity.value in ("Low", "Medium") else "medium",
                    "code_example": (
                        "# Safe pattern example:\n"
                        f"# Always sanitize inputs and use parameterized queries for {rule.id}"
                    ),
                })
            else:
                # Provide general priority recommendations across all high/critical rules
                prio = 1
                for r in SECURITY_RULES:
                    if r.severity.value in ("Critical", "High"):
                        recommendations.append({
                            "priority": prio,
                            "finding_id": r.id,
                            "title": r.title,
                            "severity": r.severity.value,
                            "cwe": r.cwe_id,
                            "remediation": r.fix_guidance,
                            "effort": "medium",
                        })
                        prio += 1

            # Optional AI Gateway Security Synthesis
            llm_insights = None
            try:
                from backend.app.config import settings
                if settings.GEMINI_API_KEY:
                    from backend.app.gateway.router import GatewayTask, ModelRouter
                    from backend.app.gateway.base_provider import Message, MessageRole
                    from backend.app.prompts.renderer import PromptRenderer

                    renderer = PromptRenderer()
                    rendered_prompt = renderer.render(
                        "security_agent.j2",
                        {
                            "agent_name": self.name,
                            "agent_purpose": self.purpose,
                            "instruction": task.instruction,
                            "target": target_rule_id or "General Rules",
                            "total_findings": len(recommendations),
                            "top_findings": [
                                {"rule_id": r["finding_id"], "severity": r["severity"], "title": r["title"], "file": "codebase", "line": 0, "snippet": r["remediation"]}
                                for r in recommendations[:3]
                            ],
                        },
                    )
                    router = ModelRouter()
                    gw_task = GatewayTask(complexity="complex", requires_reasoning=True)
                    llm_res = await router.execute_with_fallback(
                        messages=[Message(role=MessageRole.USER, content=rendered_prompt)],
                        task=gw_task,
                        max_tokens=1000,
                    )
                    llm_insights = llm_res.content
            except Exception:
                pass

            suggest_report = {
                "scan_type": "remediation_guidance",
                "target": target_rule_id or "general_remediation",
                "recommendations": recommendations,
                "llm_remediation_insights": llm_insights,
                "note": "Manual review required. Apply patches in dev branch and verify tests before deployment.",
            }

            evidence_items.append(
                Evidence(
                    source="security_rules_catalog",
                    snippet=f"Generated remediation guidance for {len(recommendations)} security rules",
                    confidence=1.0,
                )
            )

            return AgentResult(
                success=True,
                output=json.dumps(suggest_report, indent=2),
                artifacts=artifacts,
                evidence=evidence_items,
                limitations=self.limitations,
                simulated=False,
            )

        # -------------------------------------------------------------
        # READ_ONLY Tasks: Specific Tool Dispatches
        # -------------------------------------------------------------
        # 1. Secret detection only
        if "secret" in instruction or "credential" in instruction:
            secret_res = await self.secret_detector.execute(
                {"path": target_path} if target_path else {},
                context,
            )
            for ev in secret_res.evidence:
                evidence_items.append(Evidence(source="secret_detector", snippet=ev, confidence=1.0))

            output_data = {
                "scan_type": "secret_audit",
                "scanned_at": datetime.now(timezone.utc).isoformat(),
                "summary": secret_res.output,
            }
            return AgentResult(
                success=secret_res.success,
                output=json.dumps(output_data, indent=2),
                artifacts=artifacts,
                evidence=evidence_items,
                limitations=self.limitations,
                simulated=False,
            )

        # 2. Auth audit only
        if "auth" in instruction or "permission" in instruction or "jwt" in instruction:
            auth_res = await self.auth_auditor.execute({}, context)
            for ev in auth_res.evidence:
                evidence_items.append(Evidence(source="auth_auditor", snippet=ev, confidence=1.0))

            output_data = {
                "scan_type": "auth_audit",
                "scanned_at": datetime.now(timezone.utc).isoformat(),
                "summary": auth_res.output,
            }
            return AgentResult(
                success=auth_res.success,
                output=json.dumps(output_data, indent=2),
                artifacts=artifacts,
                evidence=evidence_items,
                limitations=self.limitations,
                simulated=False,
            )

        # 3. Dependency audit only
        if "dependenc" in instruction or "cve" in instruction or "package" in instruction:
            dep_res = await self.dependency_auditor.execute({}, context)
            for ev in dep_res.evidence:
                evidence_items.append(Evidence(source="dependency_auditor", snippet=ev, confidence=1.0))

            output_data = {
                "scan_type": "dependency_audit",
                "scanned_at": datetime.now(timezone.utc).isoformat(),
                "summary": dep_res.output,
            }
            return AgentResult(
                success=dep_res.success,
                output=json.dumps(output_data, indent=2),
                artifacts=artifacts,
                evidence=evidence_items,
                limitations=self.limitations,
                simulated=False,
            )

        # 4. Single file code scan
        if target_path and ("file" in instruction or target_path.endswith((".py", ".ts", ".tsx"))):
            scanner_res = await self.security_scanner.execute(
                {"path": target_path},
                context,
            )
            for ev in scanner_res.evidence:
                evidence_items.append(Evidence(source="security_scanner", snippet=ev, confidence=1.0))

            output_data = {
                "scan_type": "file_security_scan",
                "target": target_path,
                "scanned_at": datetime.now(timezone.utc).isoformat(),
                "results": scanner_res.output,
            }
            return AgentResult(
                success=scanner_res.success,
                output=json.dumps(output_data, indent=2),
                artifacts=artifacts,
                evidence=evidence_items,
                limitations=self.limitations,
                simulated=False,
            )

        # 5. Full Security Review (Default: Run all 4 tools in sequence)
        scanner_res = await self.security_scanner.execute(
            {"path": target_path} if target_path else {},
            context,
        )
        auth_res = await self.auth_auditor.execute({}, context)
        dep_res = await self.dependency_auditor.execute({}, context)
        secret_res = await self.secret_detector.execute(
            {"path": target_path} if target_path else {},
            context,
        )

        # Collate evidence
        for ev in scanner_res.evidence:
            evidence_items.append(Evidence(source="security_scanner", snippet=ev, confidence=1.0))
        for ev in auth_res.evidence:
            evidence_items.append(Evidence(source="auth_auditor", snippet=ev, confidence=1.0))
        for ev in dep_res.evidence:
            evidence_items.append(Evidence(source="dependency_auditor", snippet=ev, confidence=1.0))
        for ev in secret_res.evidence:
            evidence_items.append(Evidence(source="secret_detector", snippet=ev, confidence=1.0))

        scanner_out = scanner_res.output if isinstance(scanner_res.output, dict) else {}
        auth_out = auth_res.output if isinstance(auth_res.output, dict) else {}
        dep_out = dep_res.output if isinstance(dep_res.output, dict) else {}
        secret_out = secret_res.output if isinstance(secret_res.output, dict) else {}

        by_severity = scanner_out.get("by_severity", {
            "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0
        })

        findings = scanner_out.get("findings", [])
        total_findings = len(findings)

        # Generate top remediation recommendations
        recommendations = []
        prio = 1
        seen_rules = set()
        for f in findings:
            r_id = f.get("rule_id")
            if r_id and r_id not in seen_rules and f.get("severity") in ("Critical", "High", "critical", "high"):
                seen_rules.add(r_id)
                recommendations.append({
                    "priority": prio,
                    "finding_id": r_id,
                    "title": f.get("title", "Security Flaw"),
                    "action": f.get("fix", "Review and patch code"),
                    "effort": "medium",
                })
                prio += 1

        full_report = {
            "scan_type": "full_security_review",
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_findings": total_findings,
                "critical": by_severity.get("critical", 0),
                "high": by_severity.get("high", 0),
                "medium": by_severity.get("medium", 0),
                "low": by_severity.get("low", 0),
                "secrets_detected": secret_out.get("total_secrets", 0),
                "auth_issues": auth_out.get("failed", 0),
                "dependency_issues": dep_out.get("total_dependency_findings", 0),
            },
            "findings": findings,
            "auth_audit": auth_out,
            "dependency_audit": dep_out,
            "recommendations": recommendations,
        }

        # Create report artifact
        artifacts.append(
            Artifact(
                name="security_audit_report.json",
                artifact_type="security_report",
                content=json.dumps(full_report, indent=2),
                metadata={"total_findings": total_findings},
            )
        )

        return AgentResult(
            success=True,
            output=json.dumps(full_report, indent=2),
            artifacts=artifacts,
            evidence=evidence_items,
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
