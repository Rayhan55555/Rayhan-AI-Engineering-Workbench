"""Docker Validator Tool for Dockerfile and docker-compose analysis.

Inspects container definitions for security vulnerabilities, best practices,
layer optimizations, and reliability settings.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import re
import yaml
from pydantic import BaseModel, Field


class DockerFinding(BaseModel):
    """Detailed finding from Docker file inspection."""

    id: str
    severity: str  # "INFO", "WARNING", "HIGH", "CRITICAL"
    category: str  # "security", "best_practice", "optimization", "reliability"
    message: str
    line: Optional[int] = None
    suggestion: str


class DockerAnalysisResult(BaseModel):
    """Aggregated report of Docker configuration audit."""

    dockerfile_score: int = Field(ge=0, le=100)
    findings: List[DockerFinding] = Field(default_factory=list)
    best_practices: List[str] = Field(default_factory=list)
    security_issues: List[str] = Field(default_factory=list)
    optimizations: List[str] = Field(default_factory=list)
    compose_summary: Optional[Dict[str, Any]] = None


class DockerValidator:
    """Audits Dockerfile and docker-compose.yml files."""

    SUSPICIOUS_SECRETS_PATTERN = re.compile(
        r"(SECRET_KEY|API_KEY|PASSWORD|TOKEN|ACCESS_TOKEN|PRIVATE_KEY)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?",
        re.IGNORECASE,
    )

    @classmethod
    def analyze_dockerfile(cls, content: str) -> DockerAnalysisResult:
        """Audit a Dockerfile content string and produce score and findings."""
        lines = content.splitlines()
        findings: List[DockerFinding] = []
        best_practices: List[str] = []
        security_issues: List[str] = []
        optimizations: List[str] = []

        base_score = 100

        has_from = False
        base_image = ""
        has_user = False
        has_healthcheck = False
        has_add = False
        has_apt_clean = False
        has_multi_stage = False
        has_pip_no_cache = False

        from_count = 0

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # FROM check
            if stripped.upper().startswith("FROM "):
                has_from = True
                from_count += 1
                parts = stripped.split()
                if len(parts) >= 2:
                    base_image = parts[1]
                if " AS " in stripped.upper():
                    has_multi_stage = True

            # ADD vs COPY
            if stripped.upper().startswith("ADD "):
                has_add = True
                # Check if it's unpacking a tarball or remote URL
                if not any(ext in stripped for ext in [".tar", ".gz", ".tgz", ".bz2", "http://", "https://"]):
                    findings.append(
                        DockerFinding(
                            id="DOCKER-001",
                            severity="WARNING",
                            category="best_practice",
                            message="Use COPY instead of ADD for simple file copying.",
                            line=idx,
                            suggestion="Replace ADD with COPY unless auto-extracting compressed archives.",
                        )
                    )
                    base_score -= 5

            # USER check
            if stripped.upper().startswith("USER "):
                user_val = stripped.split(None, 1)[1].strip()
                if user_val.lower() not in ["root", "0"]:
                    has_user = True

            # HEALTHCHECK check
            if stripped.upper().startswith("HEALTHCHECK "):
                has_healthcheck = True

            # apt clean check
            if "apt-get" in stripped:
                if "rm -rf /var/lib/apt/lists/*" in stripped:
                    has_apt_clean = True
                else:
                    optimizations.append("Clean apt cache after install: 'rm -rf /var/lib/apt/lists/*'")
                    base_score -= 5

            # pip no-cache check
            if "pip install" in stripped:
                if "--no-cache-dir" in stripped:
                    has_pip_no_cache = True
                else:
                    optimizations.append("Add '--no-cache-dir' to pip install commands to reduce image layers.")
                    base_score -= 5

            # Hardcoded secrets detection
            secret_match = cls.SUSPICIOUS_SECRETS_PATTERN.search(stripped)
            if secret_match and not stripped.startswith("ARG ") and "$" not in stripped:
                secret_name = secret_match.group(1)
                security_issues.append(f"Potential hardcoded secret '{secret_name}' on line {idx}")
                findings.append(
                    DockerFinding(
                        id="DOCKER-SEC-001",
                        severity="CRITICAL",
                        category="security",
                        message=f"Hardcoded credential or key detected in Dockerfile: {secret_name}",
                        line=idx,
                        suggestion="Never hardcode credentials in container images. Use environment variables or build secrets.",
                    )
                )
                base_score -= 25

        # Base image evaluation
        if has_from:
            if any(tag in base_image for tag in [":latest", ":latest-"]):
                findings.append(
                    DockerFinding(
                        id="DOCKER-002",
                        severity="WARNING",
                        category="best_practice",
                        message=f"Avoid using ':latest' tag for base image '{base_image}'.",
                        suggestion="Pin an immutable tag or digest (e.g. 'python:3.11-slim' or SHA256 digest).",
                    )
                )
                base_score -= 10
            elif "slim" in base_image or "alpine" in base_image:
                best_practices.append(f"Minimal base image used: '{base_image}'")
            else:
                findings.append(
                    DockerFinding(
                        id="DOCKER-003",
                        severity="INFO",
                        category="optimization",
                        message=f"Standard base image '{base_image}' detected.",
                        suggestion="Consider a minimal variant like -slim or -alpine to reduce attack surface and build size.",
                    )
                )
                base_score -= 5

        # User check evaluation
        if not has_user:
            findings.append(
                DockerFinding(
                    id="DOCKER-SEC-002",
                    severity="HIGH",
                    category="security",
                    message="Container runs as default root user. No non-root USER instruction found.",
                    suggestion="Create a dedicated system user (e.g., 'RUN useradd -m appuser && USER appuser') before entrypoint.",
                )
            )
            security_issues.append("Container runs as root user; non-root user enforcement missing.")
            base_score -= 15
        else:
            best_practices.append("Non-root user configured via USER instruction.")

        # Healthcheck evaluation
        if has_healthcheck:
            best_practices.append("Explicit HEALTHCHECK instruction configured.")
        else:
            findings.append(
                DockerFinding(
                    id="DOCKER-004",
                    severity="WARNING",
                    category="reliability",
                    message="No HEALTHCHECK instruction defined in Dockerfile.",
                    suggestion="Add HEALTHCHECK to enable orchestrators (Docker, Kubernetes) to monitor container vitality.",
                )
            )
            base_score -= 10

        # Multi-stage evaluation
        if from_count > 1 or has_multi_stage:
            best_practices.append("Multi-stage build pattern utilized.")
        else:
            optimizations.append("Consider multi-stage builds to separate compiler toolchains from final runtime image.")

        if has_pip_no_cache:
            best_practices.append("pip cache disabled via '--no-cache-dir'.")

        if has_apt_clean:
            best_practices.append("apt cache cleared via 'rm -rf /var/lib/apt/lists/*'.")

        score = max(0, min(100, base_score))

        return DockerAnalysisResult(
            dockerfile_score=score,
            findings=findings,
            best_practices=best_practices,
            security_issues=security_issues,
            optimizations=optimizations,
        )

    @classmethod
    def analyze_compose(cls, content: str) -> Dict[str, Any]:
        """Audit docker-compose.yml configuration."""
        findings = []
        services_analyzed = []
        try:
            data = yaml.safe_load(content)
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to parse compose YAML: {str(e)}",
                "services": [],
                "findings": [],
            }

        if not isinstance(data, dict) or "services" not in data:
            return {"valid": False, "error": "No services block found", "services": [], "findings": []}

        services = data.get("services", {})
        for svc_name, svc_cfg in services.items():
            if not isinstance(svc_cfg, dict):
                continue
            services_analyzed.append(svc_name)
            has_healthcheck = "healthcheck" in svc_cfg
            has_limits = "deploy" in svc_cfg and "resources" in svc_cfg.get("deploy", {})
            has_restart = "restart" in svc_cfg

            if not has_healthcheck:
                findings.append({
                    "service": svc_name,
                    "severity": "WARNING",
                    "category": "reliability",
                    "message": f"Service '{svc_name}' has no healthcheck defined in compose.",
                })
            if not has_limits:
                findings.append({
                    "service": svc_name,
                    "severity": "INFO",
                    "category": "resources",
                    "message": f"Service '{svc_name}' has no resource memory/CPU limits configured.",
                })
            if not has_restart:
                findings.append({
                    "service": svc_name,
                    "severity": "INFO",
                    "category": "reliability",
                    "message": f"Service '{svc_name}' has no restart policy configured.",
                })

        return {
            "valid": True,
            "services": services_analyzed,
            "service_count": len(services_analyzed),
            "findings": findings,
        }

    @classmethod
    def analyze_project(cls, project_root: str = ".") -> DockerAnalysisResult:
        """Inspect Dockerfile and compose file from project root."""
        root = Path(project_root)
        dockerfile_candidates = [
            root / "backend" / "Dockerfile",
            root / "Dockerfile",
        ]
        dockerfile_path = None
        for cand in dockerfile_candidates:
            if cand.exists():
                dockerfile_path = cand
                break

        if dockerfile_path:
            content = dockerfile_path.read_text(encoding="utf-8")
            result = cls.analyze_dockerfile(content)
        else:
            result = DockerAnalysisResult(
                dockerfile_score=0,
                findings=[
                    DockerFinding(
                        id="DOCKER-404",
                        severity="HIGH",
                        category="best_practice",
                        message="No Dockerfile found in project repository.",
                        suggestion="Add a Dockerfile in backend/ or root to enable container deployment.",
                    )
                ],
                security_issues=["Missing Dockerfile"],
            )

        compose_candidates = [root / "docker-compose.yml", root / "docker-compose.yaml"]
        for cand in compose_candidates:
            if cand.exists():
                compose_content = cand.read_text(encoding="utf-8")
                result.compose_summary = cls.analyze_compose(compose_content)
                break

        return result
