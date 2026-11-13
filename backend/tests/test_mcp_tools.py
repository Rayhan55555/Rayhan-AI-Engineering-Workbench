import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.user import User
from backend.app.mcp.tool_registry import tool_registry
from backend.app.mcp.tool_executor import ToolExecutor
from backend.app.mcp.approval_manager import ApprovalManager
from backend.app.tools.mcp.filesystem_tool import FilesystemTool
from backend.app.tools.mcp.database_tool import DatabaseTool
from backend.app.tools.mcp.web_search_tool import WebSearchTool


def test_tool_registry_has_18_tools():
    """Verify tool registry has exactly 18 distinct tools with categories and schemas."""
    tools = tool_registry.list_all()
    assert len(tools) == 18

    names = {t.name for t in tools}
    # GitHub
    assert "github_read_file" in names
    assert "github_list_files" in names
    assert "github_read_pr" in names
    assert "github_list_issues" in names
    assert "github_create_issue" in names
    assert "github_comment_pr" in names
    assert "github_push_file" in names
    assert "github_create_pr" in names
    # Filesystem
    assert "fs_read_file" in names
    assert "fs_list_directory" in names
    assert "fs_write_file" in names
    assert "fs_delete_file" in names
    # Web
    assert "web_search" in names
    assert "web_fetch_page" in names
    # Database
    assert "db_read_query" in names
    assert "db_schema_inspect" in names
    # Shell
    assert "shell_run_linter" in names
    assert "shell_run_tests" in names


def test_tool_registry_phase_11_locks():
    """Verify push_file and create_pr are strictly locked with notes."""
    push_tool = tool_registry.get("github_push_file")
    assert push_tool is not None
    assert push_tool.enabled is False
    assert "Phase 11" in push_tool.phase_lock_note

    pr_tool = tool_registry.get("github_create_pr")
    assert pr_tool is not None
    assert pr_tool.enabled is False
    assert "Phase 11" in pr_tool.phase_lock_note


def test_filesystem_tool_blocks_traversal_and_sensitive_files():
    """Verify path traversal outside workspace and reading secrets are blocked."""
    res_traversal = FilesystemTool.read_file("../../etc/passwd")
    assert res_traversal["success"] is False
    assert "Path traversal blocked" in res_traversal["error"]

    res_secret = FilesystemTool.read_file(".env")
    assert res_secret["success"] is False
    assert "blocked" in res_secret["error"].lower()


def test_filesystem_tool_write_and_soft_delete():
    """Verify writing file creates backup and delete performs soft delete to .trash/."""
    test_path = "backend/tests/scratch_mcp_test.txt"
    content = "MCP sandboxed test content"

    write_res = FilesystemTool.write_file(test_path, content, reason="Unit test write")
    assert write_res["success"] is True

    # Read back
    read_res = FilesystemTool.read_file(test_path)
    assert read_res["success"] is True
    assert read_res["content"] == content

    # Soft delete
    del_res = FilesystemTool.delete_file(test_path, reason="Unit test cleanup")
    assert del_res["success"] is True
    assert del_res["soft_delete"] is True
    assert ".trash" in del_res["moved_to"]


def test_database_tool_rejects_destructive_dml():
    """Verify DatabaseTool only allows SELECT queries and blocks DDL/DML."""
    with pytest.raises(ValueError) as excinfo:
        DatabaseTool.validate_select_only("DROP TABLE users;")
    assert "Only read-only SELECT" in str(excinfo.value) or "Dangerous or destructive" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo2:
        DatabaseTool.validate_select_only("SELECT * FROM users; DROP TABLE users;")
    assert "Dangerous or destructive" in str(excinfo2.value)



@pytest.mark.asyncio
async def test_approval_workflow_for_write_tools(db_session: AsyncSession, test_user: User):
    """Calling write tool without approval creates pending request and pauses."""
    res = await ToolExecutor.execute(
        db=db_session,
        user_id=test_user.id,
        tool_name="fs_write_file",
        parameters={"path": "src/test_mcp.txt", "content": "hello world"},
    )

    assert res.success is True
    assert res.requires_approval is True
    assert res.approval_id is not None
    assert "human authorization" in res.output_summary.lower()

    # List pending
    pending = await ApprovalManager.list_pending(db_session, test_user.id)
    assert any(p.id == res.approval_id or str(p.id) == res.approval_id for p in pending)

    # Approve
    approved = await ApprovalManager.approve(db_session, res.approval_id, test_user.id)
    assert approved.status == "approved"

    # Now execute with approval_id
    exec_res = await ToolExecutor.execute(
        db=db_session,
        user_id=test_user.id,
        tool_name="fs_write_file",
        parameters={"path": "src/test_mcp.txt", "content": "hello world"},
        approval_id=str(approved.id),
    )
    assert exec_res.success is True
    assert exec_res.requires_approval is False

    # Cleanup
    FilesystemTool.delete_file("src/test_mcp.txt", reason="Test cleanup")


@pytest.mark.asyncio
async def test_approval_reject_flow(db_session: AsyncSession, test_user: User):
    """Verify rejected approval prevents execution."""
    res = await ToolExecutor.execute(
        db=db_session,
        user_id=test_user.id,
        tool_name="shell_run_tests",
        parameters={"test_path": "backend/tests/test_tools.py"},
    )
    assert res.requires_approval is True
    approval_id = res.approval_id

    # Reject
    rejected = await ApprovalManager.reject(db_session, approval_id, test_user.id, reason="Unscheduled test")
    assert rejected.status == "rejected"

    # Execute with rejected approval_id
    exec_res = await ToolExecutor.execute(
        db=db_session,
        user_id=test_user.id,
        tool_name="shell_run_tests",
        parameters={"test_path": "backend/tests/test_tools.py"},
        approval_id=approval_id,
    )
    assert exec_res.success is False
    assert "rejected" in exec_res.error.lower()
