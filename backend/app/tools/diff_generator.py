import difflib
from pathlib import Path
from typing import Any, Dict, List
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import (
    PROJECT_ROOT,
    SandboxSecurityError,
    resolve_safe_path,
    validate_file_extension,
)
from backend.app.tools.base_tool import BaseTool, ToolResult


class DiffGeneratorTool(BaseTool):
    name = "diff_generator"
    description = (
        "Generates unified diffs between two strings or between a target workspace file "
        "and proposed modifications. Generates patches without writing to disk."
    )
    required_permission = PermissionLevel.SUGGEST
    safe_by_default = True

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        file_path_str = params.get("path") or params.get("file_path")
        original_content = params.get("original")
        modified_content = params.get("modified")
        context_lines = params.get("context_lines", 3)

        file_label = "target_file"

        # If a file path is provided, read original from disk
        if file_path_str:
            try:
                safe_path = resolve_safe_path(str(file_path_str), PROJECT_ROOT)
                validate_file_extension(safe_path)
                file_label = str(safe_path.relative_to(PROJECT_ROOT))
                if safe_path.exists():
                    original_content = safe_path.read_text(encoding="utf-8")
                else:
                    original_content = ""
            except SandboxSecurityError as e:
                return ToolResult(
                    success=False,
                    output="",
                    error=str(e),
                    evidence=[f"Blocked diff path: {file_path_str}"],
                    simulated=False,
                )
            except Exception as e:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Error reading original file: {str(e)}",
                    evidence=[],
                    simulated=False,
                )

        if original_content is None or modified_content is None:
            return ToolResult(
                success=False,
                output="",
                error="Both 'original' (or target 'path') and 'modified' content must be provided.",
                evidence=[],
                simulated=False,
            )

        orig_lines = original_content.splitlines(keepends=True)
        mod_lines = modified_content.splitlines(keepends=True)

        diff = list(
            difflib.unified_diff(
                orig_lines,
                mod_lines,
                fromfile=f"a/{file_label}",
                tofile=f"b/{file_label}",
                n=context_lines,
            )
        )

        diff_text = "".join(diff)

        # Count added and removed lines
        lines_added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        lines_removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        return ToolResult(
            success=True,
            output=diff_text,
            evidence=[
                f"Generated unified diff for {file_label}",
                f"{lines_added} lines added, {lines_removed} lines removed",
            ],
            simulated=False,
            metadata={
                "file": file_label,
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "has_changes": bool(diff_text.strip()),
            },
        )
