import enum
from typing import Dict, List, Optional, Set, Tuple
from backend.app.agents.base_agent import TaskScope


class PermissionLevel(str, enum.Enum):
    READ_ONLY = "READ_ONLY"
    SUGGEST = "SUGGEST"
    IMPLEMENT = "IMPLEMENT"
    DEPLOY = "DEPLOY"


class ToolCategory(str, enum.Enum):
    file_read = "file_read"
    file_write = "file_write"
    code_run = "code_run"
    db_read = "db_read"
    db_write = "db_write"
    external_api = "external_api"
    deploy = "deploy"


# Phase 03/04 Scope boundary
ALLOWED_PHASE_SCOPES: Set[TaskScope] = {
    TaskScope.read_only,
    TaskScope.suggest,
}

LOCKED_PHASE_SCOPES: Set[TaskScope] = {
    TaskScope.implement,
    TaskScope.deploy,
}

# Mapping of tools to their required permission levels
TOOL_PERMISSION_MAP: Dict[str, PermissionLevel] = {
    "file_read": PermissionLevel.READ_ONLY,
    "file_reader": PermissionLevel.READ_ONLY,
    "db_read": PermissionLevel.READ_ONLY,
    "vector_search": PermissionLevel.READ_ONLY,
    "schema_lint": PermissionLevel.READ_ONLY,
    "ast_parse": PermissionLevel.READ_ONLY,
    "code_analyze": PermissionLevel.READ_ONLY,
    "code_analyzer": PermissionLevel.READ_ONLY,
    "dependency_checker": PermissionLevel.READ_ONLY,
    "diff_generator": PermissionLevel.SUGGEST,
    "test_generator": PermissionLevel.SUGGEST,
    "coverage_analyzer": PermissionLevel.READ_ONLY,
    "test_gap_detector": PermissionLevel.READ_ONLY,
    "failure_analyzer": PermissionLevel.READ_ONLY,
    "crm_sync": PermissionLevel.SUGGEST,
    "webhook_dispatch": PermissionLevel.SUGGEST,
    "file_write": PermissionLevel.IMPLEMENT,
    "code_run": PermissionLevel.IMPLEMENT,
    "test_runner": PermissionLevel.IMPLEMENT,
    "db_write": PermissionLevel.IMPLEMENT,
    "deploy": PermissionLevel.DEPLOY,
}


def check_permission(
    agent_slug: str,
    scope: TaskScope,
    requested_tools: Optional[List[str]] = None,
) -> Tuple[bool, str]:
    """
    Checks if an agent execution task is permitted under current phase guardrails.
    Returns (True, "Granted") or (False, "<Reason>").
    Never fails silently.
    """
    # 1. Scope Gate
    if scope == TaskScope.deploy:
        return (
            False,
            "Scope 'deploy' requires production release privileges which are locked until Phase 11.",
        )

    if scope == TaskScope.implement:
        # Default behavior: IMPLEMENT requires explicit approval in Phase 04
        return (
            False,
            "Scope 'implement' requires code modification capabilities which are locked until Phase 04+.",
        )

    # 2. Tool permission checks
    if requested_tools:
        for tool in requested_tools:
            required_level = TOOL_PERMISSION_MAP.get(tool.lower())
            if required_level in (PermissionLevel.IMPLEMENT, PermissionLevel.DEPLOY):
                if scope in (TaskScope.read_only, TaskScope.suggest):
                    return (
                        False,
                        f"Tool '{tool}' requires {required_level.value} permission, which is restricted in Phase 03.",
                    )

    return True, "Permission verified for Phase 03/04 runtime"

