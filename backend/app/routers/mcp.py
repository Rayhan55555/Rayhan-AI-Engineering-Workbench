from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.mcp.tool_registry import tool_registry
from backend.app.mcp.protocol import ToolCategory, ToolDefinition, ToolCallResult
from backend.app.mcp.tool_executor import ToolExecutor
from backend.app.mcp.approval_manager import ApprovalManager
from backend.app.mcp.audit_logger import AuditLogger
from backend.app.streaming.sse import mock_or_live_execution_stream
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/mcp", tags=["MCP & Tool Integrations"])


class ToolExecuteRequest(BaseModel):
    parameters: Dict[str, Any] = {}
    approval_id: Optional[str] = None
    agent_slug: Optional[str] = None


class RejectRequest(BaseModel):
    reason: Optional[str] = None


@router.get("/tools", response_model=List[ToolDefinition])
async def list_tools(
    category: Optional[ToolCategory] = None,
    current_user: User = Depends(get_current_user),
):
    """Lists all 18 MCP tools with schemas, permission scopes, and approval requirements."""
    return tool_registry.list_all(category=category)


@router.get("/tools/{name}", response_model=ToolDefinition)
async def get_tool(
    name: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieves definition and JSON input schema for a single tool."""
    tool = tool_registry.get(name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{name}' not found in registry.",
        )
    return tool


@router.post("/tools/{name}/execute", response_model=ToolCallResult)
async def execute_tool(
    name: str,
    body: ToolExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes a tool call. If the tool modifies state or runs shell commands,
    an approval request is generated and execution pauses until authorized.
    """
    result = await ToolExecutor.execute(
        db=db,
        user_id=current_user.id,
        tool_name=name,
        parameters=body.parameters,
        approval_id=body.approval_id,
        agent_slug=body.agent_slug,
    )
    return result


@router.get("/approvals")
async def list_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns all active pending tool approval requests for the current user."""
    approvals = await ApprovalManager.list_pending(db, current_user.id)
    return [
        {
            "id": str(app.id),
            "tool_name": app.tool_name,
            "agent_slug": app.agent_slug,
            "parameters": app.parameters,
            "preview": app.preview,
            "risk_level": app.risk_level,
            "status": app.status,
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "expires_at": app.expires_at.isoformat() if app.expires_at else None,
        }
        for app in approvals
    ]


@router.post("/approvals/{approval_id}/approve")
async def approve_tool_call(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approves a pending tool request."""
    try:
        app = await ApprovalManager.approve(db, approval_id, current_user.id)
        return {
            "success": True,
            "approval_id": str(app.id),
            "status": app.status,
            "message": "Tool execution authorized.",
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.post("/approvals/{approval_id}/reject")
async def reject_tool_call(
    approval_id: str,
    body: RejectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rejects a pending tool request."""
    try:
        app = await ApprovalManager.reject(db, approval_id, current_user.id, reason=body.reason)
        return {
            "success": True,
            "approval_id": str(app.id),
            "status": app.status,
            "message": "Tool execution rejected.",
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.get("/audit")
async def list_audit_trail(
    tool_name: Optional[str] = None,
    agent_slug: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves the immutable audit log for the current user.
    All parameters are strictly scrubbed of secrets.
    """
    entries = await AuditLogger.list_logs(
        db=db,
        user_id=current_user.id,
        tool_name=tool_name,
        agent_slug=agent_slug,
        limit=limit,
        offset=offset,
    )
    return [
        {
            "id": str(e.id),
            "tool_name": e.tool_name,
            "agent_slug": e.agent_slug,
            "parameters": e.parameters,
            "output_summary": e.output_summary,
            "success": e.success,
            "error_message": e.error_message,
            "duration_ms": e.duration_ms,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]


@router.get("/stream/demo")
async def sse_stream_demo(
    execution_id: str = "demo-exec-001",
    agent: str = "arch-sentinel",
):
    """SSE endpoint streaming live agent thinking, tool executions, and LLM chunks."""
    return StreamingResponse(
        mock_or_live_execution_stream(
            execution_id=execution_id,
            agent_slug=agent,
            task_description="Analyze repository architecture and verify sandbox integrity.",
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
