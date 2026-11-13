import time
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.mcp.protocol import ToolCallResult, ToolDefinition
from backend.app.mcp.tool_registry import tool_registry
from backend.app.mcp.audit_logger import AuditLogger
from backend.app.mcp.approval_manager import ApprovalManager
from backend.app.tools.mcp.github_tool import GitHubTool
from backend.app.tools.mcp.filesystem_tool import FilesystemTool
from backend.app.tools.mcp.web_search_tool import WebSearchTool
from backend.app.tools.mcp.database_tool import DatabaseTool
from backend.app.tools.mcp.shell_tool import ShellTool


class ToolExecutor:
    """
    Safe execution pipeline for all 18 MCP tools.
    Enforces registry check, approval requirement, duration measurement, and immutable auditing.
    """

    @classmethod
    async def execute(
        cls,
        db: AsyncSession,
        user_id: Any,
        tool_name: str,
        parameters: Dict[str, Any],
        approval_id: Optional[str] = None,
        agent_slug: Optional[str] = None,
    ) -> ToolCallResult:
        start_time = time.time()
        tool_def: Optional[ToolDefinition] = tool_registry.get(tool_name)

        if not tool_def:
            duration_ms = int((time.time() - start_time) * 1000)
            err_msg = f"Tool '{tool_name}' not found in registry."
            await AuditLogger.log_call(
                db=db,
                user_id=user_id,
                tool_name=tool_name,
                parameters=parameters,
                success=False,
                error_message=err_msg,
                duration_ms=duration_ms,
                agent_slug=agent_slug,
            )
            return ToolCallResult(tool_name=tool_name, success=False, error=err_msg, duration_ms=duration_ms)

        # Check phase locking
        if not tool_def.enabled or tool_def.phase_lock_note:
            duration_ms = int((time.time() - start_time) * 1000)
            note = tool_def.phase_lock_note or "This tool is disabled in the current phase."
            await AuditLogger.log_call(
                db=db,
                user_id=user_id,
                tool_name=tool_name,
                parameters=parameters,
                success=False,
                error_message=note,
                duration_ms=duration_ms,
                agent_slug=agent_slug,
            )
            return ToolCallResult(tool_name=tool_name, success=False, error=note, duration_ms=duration_ms)

        # Check approval requirement
        if tool_def.requires_approval:
            if not approval_id:
                # Generate preview diff or payload description
                preview = await cls._generate_preview(tool_name, parameters)
                approval = await ApprovalManager.create_request(
                    db=db,
                    user_id=user_id,
                    tool_name=tool_name,
                    parameters=parameters,
                    preview=preview,
                    risk_level=tool_def.risk_level.value,
                    agent_slug=agent_slug,
                )
                duration_ms = int((time.time() - start_time) * 1000)
                await AuditLogger.log_call(
                    db=db,
                    user_id=user_id,
                    tool_name=tool_name,
                    parameters=parameters,
                    output_summary=f"Approval request #{approval.id} created (risk: {approval.risk_level}).",
                    success=True,
                    duration_ms=duration_ms,
                    agent_slug=agent_slug,
                )
                return ToolCallResult(
                    tool_name=tool_name,
                    success=True,
                    requires_approval=True,
                    approval_id=str(approval.id),
                    preview=preview,
                    output_summary="Tool execution requires explicit human authorization.",
                    duration_ms=duration_ms,
                )
            else:
                # Verify approval was granted
                app_obj = await ApprovalManager.get_by_id(db, approval_id, user_id)
                if not app_obj:
                    duration_ms = int((time.time() - start_time) * 1000)
                    err = "Specified approval request does not exist."
                    return ToolCallResult(tool_name=tool_name, success=False, error=err, duration_ms=duration_ms)
                if app_obj.status != "approved":
                    duration_ms = int((time.time() - start_time) * 1000)
                    err = f"Approval request status is '{app_obj.status}'. Execution rejected."
                    return ToolCallResult(tool_name=tool_name, success=False, error=err, duration_ms=duration_ms)

        # Dispatch real tool execution
        try:
            result_data = await cls._dispatch(db, tool_name, parameters)
            duration_ms = int((time.time() - start_time) * 1000)
            is_success = result_data.get("success", True)
            err_msg = result_data.get("error")

            summary = str(result_data)[:200]
            await AuditLogger.log_call(
                db=db,
                user_id=user_id,
                tool_name=tool_name,
                parameters=parameters,
                output_summary=summary,
                success=is_success,
                error_message=err_msg,
                duration_ms=duration_ms,
                agent_slug=agent_slug,
            )

            return ToolCallResult(
                tool_name=tool_name,
                success=is_success,
                content=[{"type": "json", "data": result_data}],
                output_summary=summary,
                error=err_msg,
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            err_msg = f"Unexpected execution error: {str(e)}"
            await AuditLogger.log_call(
                db=db,
                user_id=user_id,
                tool_name=tool_name,
                parameters=parameters,
                success=False,
                error_message=err_msg,
                duration_ms=duration_ms,
                agent_slug=agent_slug,
            )
            return ToolCallResult(tool_name=tool_name, success=False, error=err_msg, duration_ms=duration_ms)

    @classmethod
    async def _generate_preview(cls, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "fs_write_file":
            path = parameters.get("path", "")
            content = parameters.get("content", "")
            diff_res = FilesystemTool.generate_diff(path, content)
            return {
                "action": "Write Workspace File",
                "target": path,
                "diff": diff_res.get("diff", ""),
                "reason": parameters.get("reason", "Code update"),
            }
        elif tool_name == "fs_delete_file":
            path = parameters.get("path", "")
            return {
                "action": "Soft-delete File to .trash/",
                "target": path,
                "reason": parameters.get("reason", "File cleanup"),
            }
        elif tool_name == "github_create_issue":
            return {
                "action": "Create GitHub Issue",
                "repo": parameters.get("repo"),
                "title": parameters.get("title"),
                "body_preview": parameters.get("body", "")[:300],
            }
        elif tool_name == "github_comment_pr":
            return {
                "action": "Post PR Review Comment",
                "repo": parameters.get("repo"),
                "pr_number": parameters.get("pr_number"),
                "comment_preview": parameters.get("comment", "")[:300],
            }
        elif tool_name == "shell_run_tests":
            return {
                "action": "Execute Test Runner",
                "command": f"pytest {parameters.get('test_path')}",
            }
        return {"action": tool_name, "parameters": parameters}

    @classmethod
    async def _dispatch(cls, db: AsyncSession, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # GitHub
        if tool_name == "github_read_file":
            return await GitHubTool.read_file(params["repo"], params["path"], params.get("branch", "main"))
        elif tool_name == "github_list_files":
            return await GitHubTool.list_files(params["repo"], params.get("path", ""), params.get("branch", "main"))
        elif tool_name == "github_read_pr":
            return await GitHubTool.read_pr(params["repo"], int(params["pr_number"]))
        elif tool_name == "github_list_issues":
            return await GitHubTool.list_issues(params["repo"], params.get("state", "open"))
        elif tool_name == "github_create_issue":
            return await GitHubTool.create_issue(params["repo"], params["title"], params["body"], params.get("labels"))
        elif tool_name == "github_comment_pr":
            return await GitHubTool.comment_pr(params["repo"], int(params["pr_number"]), params["comment"])

        # Filesystem
        elif tool_name == "fs_read_file":
            return FilesystemTool.read_file(params["path"])
        elif tool_name == "fs_list_directory":
            return FilesystemTool.list_directory(params.get("path", "."), params.get("max_depth", 3))
        elif tool_name == "fs_write_file":
            return FilesystemTool.write_file(params["path"], params["content"], params.get("reason", ""))
        elif tool_name == "fs_delete_file":
            return FilesystemTool.delete_file(params["path"], params.get("reason", ""))

        # Web
        elif tool_name == "web_search":
            return await WebSearchTool.search(params["query"], params.get("max_results", 5))
        elif tool_name == "web_fetch_page":
            return await WebSearchTool.fetch_page(params["url"])

        # Database
        elif tool_name == "db_read_query":
            return await DatabaseTool.execute_query(db, params["query"], params.get("limit", 50))
        elif tool_name == "db_schema_inspect":
            return await DatabaseTool.inspect_schema(db, params.get("table_name"))

        # Shell
        elif tool_name == "shell_run_linter":
            return await ShellTool.run_linter(params.get("target_path", "backend/app"))
        elif tool_name == "shell_run_tests":
            return await ShellTool.run_tests(params["test_path"])

        return {"success": False, "error": f"Unhandled tool dispatch: {tool_name}"}
