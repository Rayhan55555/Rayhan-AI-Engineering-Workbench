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
from backend.app.tools.test_generator import TestGeneratorTool

router = APIRouter(prefix="/testing", tags=["Testing Agent"])


class TestingAnalyzeRequest(BaseModel):
    task: Literal["coverage", "gaps", "quality", "failures"] = "coverage"
    target: str = Field(default="backend/tests", description="File or test path")
    failure_output: Optional[str] = Field(None, description="Raw failure stdout/stderr for failure analysis")


class TestGenerateRequest(BaseModel):
    target_file: str = Field(..., description="Target source module path (e.g. backend/app/routers/auth.py)")
    function_names: Optional[List[str]] = Field(default=None, description="Optional list of specific functions")


class TestRunRequest(BaseModel):
    test_path: str = Field(default="backend/tests", description="Pytest target path")
    timeout: int = Field(default=60, ge=5, le=120, description="Execution timeout in seconds")


class TestReportItem(BaseModel):
    execution_id: uuid.UUID
    task_id: uuid.UUID
    status: ExecutionStatus
    task_type: str
    target: str
    summary: Dict[str, Any]
    created_at: datetime


@router.post(
    "/analyze",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger testing analysis (coverage, gaps, quality, or failure analysis)",
)
async def analyze_testing(
    body: TestingAnalyzeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent_slug = "testing-agent"
    agent_impl = agent_registry.get(agent_slug)
    if not agent_impl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Testing agent not loaded in registry."},
        )

    instruction = f"analyze {body.task} in {body.target}"
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
            "task": body.task,
            "path": body.target,
            "failure_output": body.failure_output,
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
        "message": f"Testing analysis task '{body.task}' accepted and queued for execution.",
    }


@router.post(
    "/generate",
    summary="Generate deterministic test case templates (SUGGEST only, no auto-write to disk)",
)
async def generate_test_templates(
    body: TestGenerateRequest,
    current_user: User = Depends(get_current_user),
):
    tool = TestGeneratorTool()
    res = await tool.execute(
        {
            "target_file": body.target_file,
            "function_names": body.function_names or [],
        },
        ExecutionContext(allowed_tools=["test_generator"], dry_run=False),
    )

    if not res.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "generator_failed", "message": res.error},
        )

    return res.output


@router.post(
    "/run",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run pytest suite (requires IMPLEMENT scope approval flow)",
)
async def run_test_suite(
    body: TestRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent_slug = "testing-agent"
    agent_impl = agent_registry.get(agent_slug)
    if not agent_impl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Testing agent not loaded in registry."},
        )

    task_id = uuid.uuid4()
    instruction = f"run full test suite in {body.test_path}"

    execution = AgentExecution(
        agent_slug=agent_slug,
        task_id=task_id,
        user_id=current_user.id,
        status=ExecutionStatus.Pending,
        scope=TaskScope.implement,
        instruction=instruction,
        simulated=False,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # Note: Execution remains Pending until approved via /api/v1/executions/{id}/approve
    return {
        "execution_id": execution.id,
        "task_id": task_id,
        "status": execution.status,
        "scope": "implement",
        "simulated": False,
        "message": "Task created with IMPLEMENT scope. Approval required before execution.",
    }


@router.get(
    "/reports",
    response_model=PaginatedResponse[TestReportItem],
    summary="List past testing reports",
)
async def list_testing_reports(
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
        .where(AgentExecution.agent_slug == "testing-agent")
    )

    count_query = select(func.count()).select_from(base_query.subquery())
    total_count = (await db.execute(count_query)).scalar_one()

    query = base_query.order_by(AgentExecution.created_at.desc()).offset(offset).limit(limit)
    items = (await db.execute(query)).scalars().all()

    reports: List[TestReportItem] = []
    for item in items:
        summary_dict = {}
        task_type = "testing_task"
        if item.output:
            try:
                data = json.loads(item.output) if isinstance(item.output, str) else item.output
                if isinstance(data, dict):
                    summary_dict = data.get("summary", {})
                    task_type = data.get("task_type", task_type)
            except Exception:
                pass

        reports.append(
            TestReportItem(
                execution_id=item.id,
                task_id=item.task_id,
                status=item.status,
                task_type=task_type,
                target="backend/tests",
                summary=summary_dict,
                created_at=item.created_at,
            )
        )

    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0
    return PaginatedResponse[TestReportItem](
        items=reports,
        total=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get(
    "/reports/{execution_id}",
    summary="Get full detailed test report by execution ID",
)
async def get_test_report(
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
            detail={"error": "not_found", "message": "Test execution record not found."},
        )

    if execution.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "You do not have access to this test report."},
        )

    report_payload: Dict[str, Any] = {}
    if execution.output:
        try:
            parsed = json.loads(execution.output) if isinstance(execution.output, str) else execution.output
            report_payload = parsed if isinstance(parsed, dict) else {"raw": execution.output}
        except Exception:
            report_payload = {"raw": execution.output}

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
        "report": report_payload,
        "evidence": report_payload.get("evidence", []),
        "artifacts": report_payload.get("artifacts", []),
    }
