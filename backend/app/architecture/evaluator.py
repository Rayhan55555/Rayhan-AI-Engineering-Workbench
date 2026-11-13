from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ArchitectureFinding(BaseModel):
    category: str
    severity: str  # info, warning, error
    title: str
    description: str
    affected_components: List[str] = Field(default_factory=list)
    recommendation: str


class ArchitectureReport(BaseModel):
    analysis_type: str
    health_score: int  # 0 to 100
    grade: str  # A, B, C, D, F
    summary: str
    findings: List[ArchitectureFinding] = Field(default_factory=list)
    violations: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    diagrams: Dict[str, str] = Field(default_factory=dict)


class ArchitectureEvaluator:
    """
    Evaluates system architecture health and conformance to clean architecture principles.
    """

    @classmethod
    def calculate_health_score(
        cls,
        has_circular_deps: bool,
        circular_dep_count: int,
        layer_violations: List[str],
        undocumented_routes_count: int,
        total_routes_count: int,
        has_immutable_audit: bool,
        has_gateway_fallback: bool,
    ) -> ArchitectureReport:
        score = 100
        findings: List[ArchitectureFinding] = []
        violations: List[str] = list(layer_violations)
        recommendations: List[str] = []

        # 1. Circular dependencies check (-15 per cycle, max -30)
        if has_circular_deps:
            penalty = min(30, circular_dep_count * 15)
            score -= penalty
            findings.append(ArchitectureFinding(
                category="Dependencies",
                severity="error",
                title="Circular Dependencies Detected",
                description=f"Identified {circular_dep_count} cyclic module imports that impede maintainability and isolated testing.",
                recommendation="Decouple cyclic modules using dependency injection, abstract base interfaces, or event messaging.",
            ))
            recommendations.append("Break import cycles between dependent packages.")
        else:
            findings.append(ArchitectureFinding(
                category="Dependencies",
                severity="info",
                title="Zero Circular Dependencies",
                description="Python import graph is clean, unidirectional, and acyclic.",
                recommendation="Maintain current modular boundaries.",
            ))

        # 2. Layer Violations (-10 per violation, max -20)
        if layer_violations:
            penalty = min(20, len(layer_violations) * 10)
            score -= penalty
            findings.append(ArchitectureFinding(
                category="Layering",
                severity="warning",
                title="Layer Separation Concerns",
                description="Direct dependencies detected bypassing domain boundaries.",
                affected_components=layer_violations,
                recommendation="Enforce strict layered routing: Routers -> Agent Domain -> Models/Tools.",
            ))
            recommendations.append("Refactor cross-layer calls through service interfaces.")

        # 3. Documentation coverage check (-1 per 5% undocumented)
        if total_routes_count > 0:
            doc_ratio = (total_routes_count - undocumented_routes_count) / total_routes_count
            if doc_ratio < 0.8:
                penalty = int((0.8 - doc_ratio) * 20)
                score -= penalty
                findings.append(ArchitectureFinding(
                    category="API Contracts",
                    severity="warning",
                    title="API Documentation Gaps",
                    description=f"{undocumented_routes_count} of {total_routes_count} endpoints lack comprehensive docstrings or descriptions.",
                    recommendation="Run Documentation Agent to backfill OpenAPI endpoint docstrings and parameter schemas.",
                ))
                recommendations.append("Enrich endpoint docstrings for all public routes.")

        # 4. Core Security & Fault Tolerance validation
        if not has_immutable_audit:
            score -= 15
            findings.append(ArchitectureFinding(
                category="Compliance",
                severity="error",
                title="Missing Immutable Audit Trail",
                description="Tool invocations are not logged to an append-only store.",
                recommendation="Enable ToolAudit logging in all tool dispatch paths.",
            ))
            recommendations.append("Verify append-only logging for MCP tool executions.")

        if not has_gateway_fallback:
            score -= 10
            findings.append(ArchitectureFinding(
                category="Reliability",
                severity="warning",
                title="Single Provider Exposure",
                description="AI Gateway lacks secondary fallback provider.",
                recommendation="Configure ClaudeProvider fallback chain.",
            ))

        # Clamp score
        score = max(0, min(100, score))

        # Compute grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"

        summary = (
            f"Overall Architecture Health Score: {score}/100 (Grade {grade}). "
            f"Evaluated across {total_routes_count} API endpoints, module import graph, and MCP guardrails."
        )

        return ArchitectureReport(
            analysis_type="full_system_audit",
            health_score=score,
            grade=grade,
            summary=summary,
            findings=findings,
            violations=violations,
            recommendations=recommendations,
            metrics={
                "total_routes": total_routes_count,
                "undocumented_routes": undocumented_routes_count,
                "circular_dependency_count": circular_dep_count,
                "has_circular_deps": has_circular_deps,
                "layer_violations_count": len(violations),
            },
        )
