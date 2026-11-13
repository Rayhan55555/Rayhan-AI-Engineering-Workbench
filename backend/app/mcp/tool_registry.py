from typing import Dict, List, Optional
from backend.app.mcp.protocol import (
    ToolDefinition,
    ToolCategory,
    ToolPermissionScope,
    ToolRiskLevel,
    ToolInputSchema,
)


class ToolRegistry:
    """
    Central catalog of all 18 MCP tools available in Rayhan AI Engineering Workbench.
    Enforces strict metadata, permission scopes, approval flags, and phase locking.
    """
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        # 1. GitHub Tools (8 tools)
        self.register(ToolDefinition(
            name="github_read_file",
            description="Reads file contents from a GitHub repository (under 500KB). Blocks .env and secret files.",
            category=ToolCategory.GITHUB,
            permission_scope=ToolPermissionScope.READ_ONLY,
            requires_approval=False,
            risk_level=ToolRiskLevel.LOW,
            inputSchema=ToolInputSchema(
                properties={
                    "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
                    "path": {"type": "string", "description": "File path within repository"},
                    "branch": {"type": "string", "description": "Branch name (default: main)", "default": "main"},
                },
                required=["repo", "path"]
            )
        ))

        self.register(ToolDefinition(
            name="github_list_files",
            description="Lists files and directory tree from a GitHub repository path.",
            category=ToolCategory.GITHUB,
            permission_scope=ToolPermissionScope.READ_ONLY,
            requires_approval=False,
            risk_level=ToolRiskLevel.LOW,
            inputSchema=ToolInputSchema(
                properties={
                    "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
                    "path": {"type": "string", "description": "Directory path", "default": ""},
                    "branch": {"type": "string", "description": "Branch name", "default": "main"},
                },
                required=["repo"]
            )
        ))

        self.register(ToolDefinition(
            name="github_read_pr",
            description="Reads pull request metadata, body, status, and diff summary (<50KB).",
            category=ToolCategory.GITHUB,
            permission_scope=ToolPermissionScope.READ_ONLY,
            requires_approval=False,
            risk_level=ToolRiskLevel.LOW,
            inputSchema=ToolInputSchema(
                properties={
                    "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
                    "pr_number": {"type": "integer", "description": "Pull request number"},
                },
                required=["repo", "pr_number"]
            )
        ))

        self.register(ToolDefinition(
            name="github_list_issues",
            description="Lists repository issues and filter by state or labels.",
            category=ToolCategory.GITHUB,
            permission_scope=ToolPermissionScope.READ_ONLY,
            requires_approval=False,
            risk_level=ToolRiskLevel.LOW,
            inputSchema=ToolInputSchema(
                properties={
                    "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
                    "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                },
                required=["repo"]
            )
        ))

        self.register(ToolDefinition(
            name="github_create_issue",
            description="Creates an issue on a GitHub repository. Requires explicit user authorization.",
            category=ToolCategory.GITHUB,
            permission_scope=ToolPermissionScope.IMPLEMENT,
            requires_approval=True,
            risk_level=ToolRiskLevel.MEDIUM,
            inputSchema=ToolInputSchema(
                properties={
                    "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
                    "title": {"type": "string", "description": "Issue title"},
                    "body": {"type": "string", "description": "Issue markdown body"},
                    "labels": {"type": "array", "items": {"type": "string"}, "description": "Optional labels"},
                },
                required=["repo", "title", "body"]
            )
        ))

        self.register(ToolDefinition(
            name="github_comment_pr",
            description="Posts a comment or code review feedback on a Pull Request. Requires authorization.",
            category=ToolCategory.GITHUB,
            permission_scope=ToolPermissionScope.IMPLEMENT,
            requires_approval=True,
            risk_level=ToolRiskLevel.MEDIUM,
            inputSchema=ToolInputSchema(
                properties={
                    "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
                    "pr_number": {"type": "integer", "description": "Pull request number"},
                    "comment": {"type": "string", "description": "Review comment body"},
                },
                required=["repo", "pr_number", "comment"]
            )
        ))

        self.register(ToolDefinition(
            name="github_push_file",
            description="Pushes a file commit directly to a branch. Strictly locked until Phase 11.",
            category=ToolCategory.GITHUB,
            permission_scope=ToolPermissionScope.DEPLOY,
            requires_approval=True,
            risk_level=ToolRiskLevel.CRITICAL,
            enabled=False,
            phase_lock_note="Locked: Available in Phase 11 (CI/CD & Deployment Pipeline)",
            inputSchema=ToolInputSchema(
                properties={
                    "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Commit content"},
                    "message": {"type": "string", "description": "Commit message"},
                },
                required=["repo", "path", "content", "message"]
            )
        ))

        self.register(ToolDefinition(
            name="github_create_pr",
            description="Creates a new Pull Request. Strictly locked until Phase 11.",
            category=ToolCategory.GITHUB,
            permission_scope=ToolPermissionScope.DEPLOY,
            requires_approval=True,
            risk_level=ToolRiskLevel.HIGH,
            enabled=False,
            phase_lock_note="Locked: Available in Phase 11 (CI/CD & Deployment Pipeline)",
            inputSchema=ToolInputSchema(
                properties={
                    "repo": {"type": "string", "description": "Repository in format 'owner/repo'"},
                    "title": {"type": "string", "description": "PR title"},
                    "head": {"type": "string", "description": "Head branch"},
                    "base": {"type": "string", "description": "Base branch", "default": "main"},
                },
                required=["repo", "title", "head"]
            )
        ))

        # 2. Filesystem Tools (4 tools)
        self.register(ToolDefinition(
            name="fs_read_file",
            description="Reads file from sandboxed project workspace. Enforces traversal and secret guards (<500KB).",
            category=ToolCategory.FILESYSTEM,
            permission_scope=ToolPermissionScope.READ_ONLY,
            requires_approval=False,
            risk_level=ToolRiskLevel.LOW,
            inputSchema=ToolInputSchema(
                properties={
                    "path": {"type": "string", "description": "Relative file path within workspace"},
                },
                required=["path"]
            )
        ))

        self.register(ToolDefinition(
            name="fs_list_directory",
            description="Lists workspace directory contents recursively up to depth 5, excluding build/cache artifacts.",
            category=ToolCategory.FILESYSTEM,
            permission_scope=ToolPermissionScope.READ_ONLY,
            requires_approval=False,
            risk_level=ToolRiskLevel.LOW,
            inputSchema=ToolInputSchema(
                properties={
                    "path": {"type": "string", "description": "Relative directory path", "default": "."},
                    "max_depth": {"type": "integer", "description": "Max recursion depth", "default": 3},
                },
                required=[]
            )
        ))

        self.register(ToolDefinition(
            name="fs_write_file",
            description="Writes or updates file in workspace with automated backup and diff preview. Requires approval.",
            category=ToolCategory.FILESYSTEM,
            permission_scope=ToolPermissionScope.IMPLEMENT,
            requires_approval=True,
            risk_level=ToolRiskLevel.HIGH,
            inputSchema=ToolInputSchema(
                properties={
                    "path": {"type": "string", "description": "Target relative file path"},
                    "content": {"type": "string", "description": "New file content to write"},
                    "reason": {"type": "string", "description": "Engineering rationale for change"},
                },
                required=["path", "content"]
            )
        ))

        self.register(ToolDefinition(
            name="fs_delete_file",
            description="Safely moves a workspace file to .trash/ backup directory. Requires user authorization.",
            category=ToolCategory.FILESYSTEM,
            permission_scope=ToolPermissionScope.DEPLOY,
            requires_approval=True,
            risk_level=ToolRiskLevel.CRITICAL,
            inputSchema=ToolInputSchema(
                properties={
                    "path": {"type": "string", "description": "Target relative file path to move to .trash/"},
                    "reason": {"type": "string", "description": "Reason for deletion"},
                },
                required=["path"]
            )
        ))

        # 3. Web Tools (2 tools)
        self.register(ToolDefinition(
            name="web_search",
            description="Searches technical documentation and queries via DuckDuckGo Instant Answer API (100% keyless).",
            category=ToolCategory.WEB,
            permission_scope=ToolPermissionScope.READ_ONLY,
            requires_approval=False,
            risk_level=ToolRiskLevel.LOW,
            inputSchema=ToolInputSchema(
                properties={
                    "query": {"type": "string", "description": "Search query keywords"},
                    "max_results": {"type": "integer", "description": "Max results to return", "default": 5},
                },
                required=["query"]
            )
        ))

        self.register(ToolDefinition(
            name="web_fetch_page",
            description="Fetches public web documentation page, sanitizing scripts and extracting clean text (<200KB).",
            category=ToolCategory.WEB,
            permission_scope=ToolPermissionScope.READ_ONLY,
            requires_approval=False,
            risk_level=ToolRiskLevel.LOW,
            inputSchema=ToolInputSchema(
                properties={
                    "url": {"type": "string", "description": "Target HTTP/HTTPS URL"},
                },
                required=["url"]
            )
        ))

        # 4. Database Tools (2 tools)
        self.register(ToolDefinition(
            name="db_read_query",
            description="Executes a verified read-only SELECT query against workbench database. Blocks all DDL/DML.",
            category=ToolCategory.DATABASE,
            permission_scope=ToolPermissionScope.READ_ONLY,
            requires_approval=False,
            risk_level=ToolRiskLevel.MEDIUM,
            inputSchema=ToolInputSchema(
                properties={
                    "query": {"type": "string", "description": "SQL SELECT statement"},
                    "limit": {"type": "integer", "description": "Row limit", "default": 50},
                },
                required=["query"]
            )
        ))

        self.register(ToolDefinition(
            name="db_schema_inspect",
            description="Inspects database table schemas, column data types, nullability, and primary/foreign keys.",
            category=ToolCategory.DATABASE,
            permission_scope=ToolPermissionScope.READ_ONLY,
            requires_approval=False,
            risk_level=ToolRiskLevel.LOW,
            inputSchema=ToolInputSchema(
                properties={
                    "table_name": {"type": "string", "description": "Optional specific table to inspect"},
                },
                required=[]
            )
        ))

        # 5. Shell Tools (2 tools)
        self.register(ToolDefinition(
            name="shell_run_linter",
            description="Runs read-only code quality and style checks (flake8/ruff/mypy) on target path.",
            category=ToolCategory.SHELL,
            permission_scope=ToolPermissionScope.READ_ONLY,
            requires_approval=False,
            risk_level=ToolRiskLevel.LOW,
            inputSchema=ToolInputSchema(
                properties={
                    "target_path": {"type": "string", "description": "Path to lint", "default": "backend/app"},
                },
                required=[]
            )
        ))

        self.register(ToolDefinition(
            name="shell_run_tests",
            description="Runs scoped pytest test suite on specified test file or marker. Requires user authorization.",
            category=ToolCategory.SHELL,
            permission_scope=ToolPermissionScope.IMPLEMENT,
            requires_approval=True,
            risk_level=ToolRiskLevel.MEDIUM,
            inputSchema=ToolInputSchema(
                properties={
                    "test_path": {"type": "string", "description": "Specific test file path e.g. 'backend/tests/test_tools.py'"},
                },
                required=["test_path"]
            )
        ))

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_all(self, category: Optional[ToolCategory] = None) -> List[ToolDefinition]:
        if category:
            return [t for t in self._tools.values() if t.category == category]
        return list(self._tools.values())

    def count(self) -> int:
        return len(self._tools)


# Global singleton instance
tool_registry = ToolRegistry()
