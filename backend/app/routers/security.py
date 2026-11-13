from datetime import datetime, timezone
import json
import math
from typing import Any, Dict, List, Literal, Optional
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.agents.base_agent import (
    AgentTask,
    ExecutionContext,
    TaskScope,
)
from backend.app.agents.registry import agent_registry
from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.agent_execution import AgentExecution, ExecutionStatus
from backend.app.models.user import User
from backend.app.routers.executions import run_agent_in_background
from backend.app.schemas.common import PaginatedResponse
from backend.app.security.rules import SECURITY_RULES, SecurityRule


router = APIRouter(prefix="/security", tags=["Security Agent"])


class SecurityScanRequest(BaseModel):
    target: Literal["file", "project"] = "project"
    path: Optional[str] = Field(None, description="Relative file path if target is 'file'")
    scan_types: List[str] = Field(
        default=["code", "secrets", "auth", "deps"],
        description="Types of scans to run: code, secrets, auth, deps",
    )


class SecurityScanSummary(BaseModel):
    execution_id: uuid.UUID
    task_id: uuid.UUID
    status: ExecutionStatus
    target: str
    total_findings: int
    critical: int
    high: int
    medium: int
    low: int
    created_at: datetime


@router.get(
    "/rules",
    response_model=List[SecurityRule],
    summary="Get security rule catalog with CWE mappings and fix guidance",
)
async def get_security_rules(
    current_user: User = Depends(get_current_user),
):
    return SECURITY_RULES


@router.post(
    "/scan",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a security scan via SecurityAgent in background",
)
async def trigger_security_scan(
    body: SecurityScanRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent_slug = "security-agent"
    agent_impl = agent_registry.get(agent_slug)
    if not agent_impl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Security agent implementation not found."},
        )

    # Build human-readable instruction based on target & scan types
    types_str = ", ".join(body.scan_types)
    if body.target == "file" and body.path:
        instruction = f"scan file {body.path} for security issues ({types_str})"
    else:
        instruction = f"full security review ({types_str})"

    task_id = uuid.uuid4()
    execution = AgentExecution(
        agent_slug=agent_slug,
        task_id=task_id,
        user_id=current_user.id,
        status=ExecutionStatus.Pending,
        scope=TaskScope.read_only,
        instruction=instruction,
        simulated=False,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    task = AgentTask(
        task_id=task_id,
        agent_slug=agent_slug,
        instruction=instruction,
        scope=TaskScope.read_only,
        context={
            "target": body.target,
            "path": body.path,
            "scan_types": body.scan_types,
        },
        requested_by=current_user.id,
    )
    context = ExecutionContext(
        allowed_tools=agent_impl.allowed_tools,
        dry_run=False,
    )

    background_tasks.add_task(
        run_agent_in_background,
        agent_slug=agent_slug,
        task=task,
        context=context,
        execution_id=execution.id,
    )

    return {
        "execution_id": execution.id,
        "task_id": task_id,
        "status": execution.status,
        "simulated": False,
        "message": "Security scan task accepted and running in background.",
    }


@router.get(
    "/scans",
    response_model=PaginatedResponse[SecurityScanSummary],
    summary="List past security scans with aggregated severity counts",
)
async def list_security_scans(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    limit = min(limit, 50)
    offset = (page - 1) * limit

    base_query = (
        select(AgentExecution)
        .where(AgentExecution.user_id == current_user.id)
        .where(AgentExecution.agent_slug == "security-agent")
    )

    count_query = select(func.count()).select_from(base_query.subquery())
    total_count = (await db.execute(count_query)).scalar_one()

    query = base_query.order_by(AgentExecution.created_at.desc()).offset(offset).limit(limit)
    items = (await db.execute(query)).scalars().all()

    summaries: List[SecurityScanSummary] = []
    for item in items:
        tot = 0
        crit = 0
        high = 0
        med = 0
        low = 0
        if item.output:
            try:
                res_data = json.loads(item.output) if isinstance(item.output, str) else item.output
                if isinstance(res_data, dict):
                    summary_obj = res_data.get("summary", {})
                    tot = summary_obj.get("total_findings", 0)
                    crit = summary_obj.get("critical", 0)
                    high = summary_obj.get("high", 0)
                    med = summary_obj.get("medium", 0)
                    low = summary_obj.get("low", 0)
            except Exception:
                pass

        summaries.append(
            SecurityScanSummary(
                execution_id=item.id,
                task_id=item.task_id,
                status=item.status,
                target="project",
                total_findings=tot,
                critical=crit,
                high=high,
                medium=med,
                low=low,
                created_at=item.created_at,
            )
        )

    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0
    return PaginatedResponse[SecurityScanSummary](
        items=summaries,
        total=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get(
    "/scans/{execution_id}",
    summary="Get detailed security scan findings and report by execution ID",
)
async def get_security_scan(
    execution_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(AgentExecution).where(AgentExecution.id == execution_id)
    )
    execution = res.scalars().first()
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Security scan record not found."},
        )

    # Ownership check
    if execution.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "You do not have permission to view this scan."},
        )

    report_data: Dict[str, Any] = {}
    if execution.output:
        try:
            parsed = json.loads(execution.output) if isinstance(execution.output, str) else execution.output
            report_data = parsed if isinstance(parsed, dict) else {"raw_output": execution.output}
        except Exception:
            report_data = {"raw_output": execution.output}

    return {
        "execution_id": execution.id,
        "task_id": execution.task_id,
        "agent": execution.agent_slug,
        "status": execution.status,
        "scope": execution.scope,
        "simulated": execution.simulated,
        "instruction": execution.instruction,
        "created_at": execution.created_at,
        "completed_at": execution.completed_at,
        "error_message": execution.error_message,
        "report": report_data,
        "evidence": report_data.get("evidence", []),
        "artifacts": report_data.get("artifacts", []),
    }
