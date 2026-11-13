"""CI/CD Pipeline Generator Tool for GitHub Actions workflows.

Validates and generates production-ready YAML workflows adhering to workbench standards.
"""

from typing import Dict, Any, Optional, List
import yaml
from pydantic import BaseModel, Field

try:
    from backend.app.devops.templates import CICDTemplates
except ImportError:
    from app.devops.templates import CICDTemplates


class GeneratedWorkflow(BaseModel):
    """Details of a generated workflow file."""

    filename: str
    workflow_type: str
    yaml_content: str
    is_valid_yaml: bool
    job_count: int
    triggers: List[str]
    has_approval_gate: bool
    description: str


class CICDGenerator:
    """Generates and validates GitHub Actions CI/CD workflows."""

    SUPPORTED_TYPES = ["ci", "cd", "pr", "security", "all"]

    @classmethod
    def generate_workflow(
        cls, workflow_type: str, project_name: str = "workbench"
    ) -> GeneratedWorkflow:
        """Generate a single workflow YAML by type ('ci', 'cd', 'pr', 'security')."""
        wf_type = workflow_type.lower().strip()
        if wf_type not in ["ci", "cd", "pr", "security"]:
            raise ValueError(
                f"Unsupported workflow type '{workflow_type}'. Supported: ['ci', 'cd', 'pr', 'security']"
            )

        if wf_type == "ci":
            filename = "ci.yml"
            yaml_content = CICDTemplates.get_ci_workflow(project_name)
            desc = "Automated continuous integration suite: linting, pytest suite, security scan, and Docker build validation."
        elif wf_type == "cd":
            filename = "cd.yml"
            yaml_content = CICDTemplates.get_cd_workflow(project_name)
            desc = "Continuous delivery pipeline with staging validation, database migrations, and approval-gated production deploy."
        elif wf_type == "pr":
            filename = "pr-check.yml"
            yaml_content = CICDTemplates.get_pr_check_workflow(project_name)
            desc = "Pull request fast-feedback validation: TypeScript checks, Python formatting, and core pytest suite."
        elif wf_type == "security":
            filename = "security.yml"
            yaml_content = CICDTemplates.get_security_workflow(project_name)
            desc = "Scheduled weekly vulnerability scanning, TruffleHog git secret detection, and container audit."

        is_valid, parsed = cls.validate_yaml(yaml_content)
        jobs = list(parsed.get("jobs", {}).keys()) if isinstance(parsed, dict) else []
        triggers = []
        if isinstance(parsed, dict) and "on" in parsed:
            raw_on = parsed["on"]
            if isinstance(raw_on, dict):
                triggers = list(raw_on.keys())
            elif isinstance(raw_on, list):
                triggers = raw_on
            elif isinstance(raw_on, str):
                triggers = [raw_on]

        has_approval_gate = (
            wf_type == "cd"
            or "environment" in yaml_content.lower()
            or "approval" in yaml_content.lower()
        )

        return GeneratedWorkflow(
            filename=filename,
            workflow_type=wf_type,
            yaml_content=yaml_content,
            is_valid_yaml=is_valid,
            job_count=len(jobs),
            triggers=triggers,
            has_approval_gate=has_approval_gate,
            description=desc,
        )

    @classmethod
    def generate_all(cls, project_name: str = "workbench") -> Dict[str, GeneratedWorkflow]:
        """Generate all 4 standard workflows."""
        return {
            "ci": cls.generate_workflow("ci", project_name),
            "cd": cls.generate_workflow("cd", project_name),
            "pr": cls.generate_workflow("pr", project_name),
            "security": cls.generate_workflow("security", project_name),
        }

    @staticmethod
    def validate_yaml(yaml_str: str) -> tuple[bool, Dict[str, Any]]:
        """Validate YAML syntax and structure."""
        try:
            parsed = yaml.safe_load(yaml_str)
            return True, parsed if isinstance(parsed, dict) else {}
        except Exception:
            return False, {}
