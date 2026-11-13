"""Environment management and deployment isolation configs for Phase 11."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class EnvironmentType(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentConfig(BaseModel):
    """Configuration and guardrails for target deployment environments."""

    name: EnvironmentType
    display_name: str
    description: str
    requires_approval: bool = False
    requires_superuser: bool = False
    allowed_source_branches: List[str] = Field(default_factory=list)
    supports_rollback: bool = True
    base_url: Optional[str] = None
    health_check_endpoint: str = "/api/v1/health"
    min_replicas: int = 1
    max_replicas: int = 1
    rate_limit_enabled: bool = True
    strict_checklist: bool = True


ENVIRONMENTS: Dict[EnvironmentType, EnvironmentConfig] = {
    EnvironmentType.LOCAL: EnvironmentConfig(
        name=EnvironmentType.LOCAL,
        display_name="Local Development",
        description="Containerized local environment running Vite & FastAPI on localhost.",
        requires_approval=False,
        requires_superuser=False,
        allowed_source_branches=["*"],
        supports_rollback=False,
        base_url="http://localhost:8000",
        min_replicas=1,
        max_replicas=1,
        rate_limit_enabled=False,
        strict_checklist=False,
    ),
    EnvironmentType.STAGING: EnvironmentConfig(
        name=EnvironmentType.STAGING,
        display_name="Staging / Pre-Production",
        description="Mirror of production with test databases and integration smoke checks.",
        requires_approval=True,
        requires_superuser=False,
        allowed_source_branches=["develop", "main", "feature/*", "release/*"],
        supports_rollback=True,
        base_url="https://staging.workbench.internal",
        min_replicas=2,
        max_replicas=4,
        rate_limit_enabled=True,
        strict_checklist=True,
    ),
    EnvironmentType.PRODUCTION: EnvironmentConfig(
        name=EnvironmentType.PRODUCTION,
        display_name="Production High-Availability",
        description="Live customer-facing environment requiring explicit superuser authorization.",
        requires_approval=True,
        requires_superuser=True,
        allowed_source_branches=["main"],
        supports_rollback=True,
        base_url="https://workbench.internal",
        min_replicas=3,
        max_replicas=10,
        rate_limit_enabled=True,
        strict_checklist=True,
    ),
}


def get_environment_config(env: EnvironmentType | str) -> EnvironmentConfig:
    """Retrieve environment configuration by enum or string."""
    if isinstance(env, str):
        try:
            env = EnvironmentType(env.lower())
        except ValueError:
            raise ValueError(f"Unknown environment: {env}. Valid options: {[e.value for e in EnvironmentType]}")
    return ENVIRONMENTS[env]
