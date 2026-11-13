from pathlib import Path
from typing import Any, Dict
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel
from backend.app.sandbox.restrictions import (
    MAX_FILE_SIZE_BYTES,
    PROJECT_ROOT,
    SandboxSecurityError,
    resolve_safe_path,
    validate_file_extension,
)
from backend.app.tools.base_tool import BaseTool, ToolResult


class FileReaderTool(BaseTool):
    name = "file_reader"
    description = (
        "Safely reads a source code or config file from the workspace root. "
        "Enforces path traversal prevention, extension whitelist, and size checks."
    )
    required_permission = PermissionLevel.READ_ONLY
    safe_by_default = True

    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        file_path_str = params.get("path") or params.get("file_path")
        if not file_path_str:
            return ToolResult(
                success=False,
                output="",
                error="Parameter 'path' is required.",
                evidence=[],
                simulated=False,
            )

        try:
            safe_path = resolve_safe_path(str(file_path_str), PROJECT_ROOT)
        except SandboxSecurityError as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                evidence=[f"Blocked access attempt: {file_path_str}"],
                simulated=False,
            )

        if not safe_path.exists():
            return ToolResult(
                success=False,
                output="",
                error=f"File not found: '{file_path_str}'.",
                evidence=[f"Checked path: {safe_path}"],
                simulated=False,
            )

        if not safe_path.is_file():
            return ToolResult(
                success=False,
                output="",
                error=f"Path is not a regular file: '{file_path_str}'.",
                evidence=[f"Checked path: {safe_path}"],
                simulated=False,
            )

        # Validate extension
        try:
            validate_file_extension(safe_path)
        except SandboxSecurityError as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                evidence=[f"Rejected extension for: {safe_path.name}"],
                simulated=False,
            )

        # Check file size
        file_size = safe_path.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            return ToolResult(
                success=False,
                output="",
                error=(
                    f"File size {file_size} bytes exceeds max allowed "
                    f"limit of {MAX_FILE_SIZE_BYTES} bytes (500KB)."
                ),
                evidence=[f"File size: {file_size} bytes"],
                simulated=False,
            )

        # Read content (reject binary)
        try:
            content = safe_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                output="",
                error="Binary or non-UTF-8 file format detected. Only text files can be read.",
                evidence=[f"Encoding error reading {safe_path.name}"],
                simulated=False,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Error reading file: {str(e)}",
                evidence=[f"Read error: {str(e)}"],
                simulated=False,
            )

        rel_path = str(safe_path.relative_to(PROJECT_ROOT))
        line_count = len(content.splitlines())

        return ToolResult(
            success=True,
            output=content,
            evidence=[
                f"Read: {rel_path} ({line_count} lines, {file_size} bytes)",
            ],
            simulated=False,
            metadata={
                "filename": safe_path.name,
                "relative_path": rel_path,
                "line_count": line_count,
                "size_bytes": file_size,
                "encoding": "utf-8",
            },
        )
