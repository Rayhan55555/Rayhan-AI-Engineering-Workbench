import asyncio
import math
import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.agents.base_agent import (
    AgentTask,
    ExecutionContext,
    TaskScope,
)
from backend.app.agents.bengali_presenter import build_bengali_report
from backend.app.agents.registry import agent_registry
from backend.app.database import AsyncSessionLocal, get_db
from backend.app.dependencies import get_current_user
from backend.app.models.agent import Agent, AgentStatus
from backend.app.models.agent_execution import AgentExecution, ExecutionStatus
from backend.app.models.user import User
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.execution import (
    ExecutionApproveRequest,
    ExecutionCreate,
    ExecutionCreateResponse,
    ExecutionRead,
    ExecutionRejectRequest,
)

router = APIRouter(prefix="/executions", tags=["Agent Executions"])

IMPLEMENT_SUPPORTED_AGENTS = {
    "arch-sentinel",
    "testing-agent",
    "architecture-agent",
    "documentation-agent",
    "rag-engine-v1",
    "devops-agent",
    "masterclass-synth",
}


def _serialize_execution(execution: AgentExecution) -> ExecutionRead:
    schema_obj = ExecutionRead.model_validate(execution)
    schema_obj.bn_report = build_bengali_report(
        agent_slug=execution.agent_slug,
        instruction=execution.instruction,
        scope=execution.scope.value if hasattr(execution.scope, "value") else str(execution.scope),
        status_value=execution.status.value if hasattr(execution.status, "value") else str(execution.status),
        output=execution.output,
        error_message=execution.error_message,
        simulated=bool(execution.simulated),
    )
    return schema_obj


async def run_agent_in_background(
    agent_slug: str,
    task: AgentTask,
    context: ExecutionContext,
    execution_id: uuid.UUID,
):
    """Background runner with its own dedicated async session."""
    agent = agent_registry.get(agent_slug)
    if not agent:
        return

    import backend.app.database as db_mod
    async with db_mod.AsyncSessionLocal() as session:
        try:
            await agent.run(
                task=task,
                context=context,
                db=session,
                execution_id=execution_id,
            )
        except Exception as e:
            import logging
            logging.error(f"Background task execution failed: {e}", exc_info=True)


@router.post(
    "",
    response_model=ExecutionCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a task to an agent for background execution",
)
async def submit_execution(
    body: ExecutionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Validate Scope Gate
    norm_slug = body.agent_slug.lower().strip()
    if body.scope == TaskScope.deploy:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "scope_restricted",
                "message": f"Execution scope '{body.scope.value}' is locked until Phase 11.",
                "status_code": 403,
            },
        )
    if body.scope == TaskScope.implement and norm_slug not in IMPLEMENT_SUPPORTED_AGENTS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "scope_restricted",
                "message": (
                    f"Execution scope 'implement' is not enabled for '{norm_slug}'. Use 'read_only' or 'suggest'."
                ),
                "status_code": 403,
            },
        )

    # 2. Check Agent Status in Database
    agent_impl = agent_registry.get(norm_slug)
    agent_res = await db.execute(
        select(Agent).where(Agent.slug == norm_slug)
    )
    db_agent = agent_res.scalars().first()
    if not db_agent:
        if agent_impl and norm_slug in (
            "security-agent",
            "testing-agent",
            "architecture-agent",
            "documentation-agent",
            "devops-agent",
        ):
            db_agent = Agent(
                slug=agent_impl.slug,
                name=agent_impl.name,
                purpose=agent_impl.purpose,
                status=AgentStatus.Available,
                allowed_tools=list(agent_impl.allowed_tools),
                phase=agent_impl.phase,
                limitations=list(agent_impl.limitations),
            )
            db.add(db_agent)
            await db.commit()
            await db.refresh(db_agent)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "message": f"Agent '{body.agent_slug}' not found in registry.",
                    "status_code": 404,
                },
            )

    if db_agent.status != AgentStatus.Available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "agent_not_available",
                "message": f"Cannot submit task to agent with status '{db_agent.status.value}'. Agent must be 'Available'.",
                "status_code": 400,
            },
        )

    # Check agent implementation in code registry
    if not agent_impl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": f"Agent implementation '{body.agent_slug}' not loaded in runtime registry.",
                "status_code": 404,
            },
        )

    # 3. Create AgentExecution Record in DB
    # Truthful label: implemented agents execute real tools (simulated=False)
    is_simulated = norm_slug not in (
        "arch-sentinel",
        "security-agent",
        "testing-agent",
        "architecture-agent",
        "documentation-agent",
        "rag-engine-v1",
        "devops-agent",
        "masterclass-synth",
        "eval-matrix",
    )

    task_id = uuid.uuid4()
    execution = AgentExecution(
        agent_slug=db_agent.slug,
        task_id=task_id,
        user_id=current_user.id,
        status=ExecutionStatus.Pending,
        scope=body.scope,
        instruction=body.instruction,
        simulated=is_simulated,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # 4. Prepare Task and Context
    task = AgentTask(
        task_id=task_id,
        agent_slug=db_agent.slug,
        instruction=body.instruction,
        scope=body.scope,
        context=body.context or {},
        requested_by=current_user.id,
    )
    context = ExecutionContext(
        project_id=body.project_id,
        allowed_tools=agent_impl.allowed_tools,
        dry_run=False,
    )

    # 5. Enqueue background execution
    # Note: If implement scope, execution is created as Pending and waits for POST /approve
    # unless already pre-approved in context.
    if body.scope == TaskScope.implement and not body.context.get("pre_approved"):
        # Execution remains in Pending state waiting for /approve call
        return ExecutionCreateResponse(
            execution_id=execution.id,
            task_id=task_id,
            agent_slug=db_agent.slug,
            status=ExecutionStatus.Pending,
            simulated=is_simulated,
            message="Task created with IMPLEMENT scope. Awaiting user approval at /approve endpoint.",
        )

    background_tasks.add_task(
        run_agent_in_background,
        agent_slug=db_agent.slug,
        task=task,
        context=context,
        execution_id=execution.id,
    )

    # Return 202 Accepted immediately
    return ExecutionCreateResponse(
        execution_id=execution.id,
        task_id=task_id,
        agent_slug=db_agent.slug,
        status=ExecutionStatus.Pending,
        simulated=is_simulated,
        message="Task accepted and enqueued for background lifecycle execution.",
    )


@router.get(
    "/{execution_id}",
    response_model=ExecutionRead,
    summary="Get execution status and results by ID",
)
async def get_execution(
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
            detail={
                "error": "not_found",
                "message": "Execution record not found.",
                "status_code": 404,
            },
        )

    # Ownership check
    if execution.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "message": "You do not have permission to view this execution.",
                "status_code": 403,
            },
        )

    return _serialize_execution(execution)


@router.get(
    "",
    response_model=PaginatedResponse[ExecutionRead],
    summary="List current user's agent executions with pagination",
)
async def list_executions(
    agent_slug: Optional[str] = Query(None, description="Filter by agent slug"),
    status_filter: Optional[ExecutionStatus] = Query(
        None, alias="status", description="Filter by execution status"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    limit = min(limit, 50)
    offset = (page - 1) * limit

    base_query = select(AgentExecution).where(AgentExecution.user_id == current_user.id)
    if agent_slug:
        base_query = base_query.where(AgentExecution.agent_slug == agent_slug.strip())
    if status_filter:
        base_query = base_query.where(AgentExecution.status == status_filter)

    count_query = select(func.count()).select_from(base_query.subquery())
    total_count = (await db.execute(count_query)).scalar_one()

    query = (
        base_query.order_by(AgentExecution.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = (await db.execute(query)).scalars().all()
    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0

    return PaginatedResponse[ExecutionRead](
        items=[_serialize_execution(item) for item in items],
        total=total_count,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.delete(
    "/{execution_id}",
    response_model=ExecutionRead,
    summary="Cancel a pending or running execution",
)
async def cancel_execution(
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
            detail={
                "error": "not_found",
                "message": "Execution record not found.",
                "status_code": 404,
            },
        )

    if execution.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "message": "You do not have permission to cancel this execution.",
                "status_code": 403,
            },
        )

    if execution.status in (ExecutionStatus.Completed, ExecutionStatus.Failed, ExecutionStatus.Cancelled):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "invalid_state",
                "message": f"Cannot cancel execution with terminal status '{execution.status.value}'.",
                "status_code": 409,
            },
        )

    execution.status = ExecutionStatus.Cancelled
    execution.error_message = "Cancelled by user."
    await db.commit()
    await db.refresh(execution)
    return _serialize_execution(execution)


@router.post(
    "/{execution_id}/approve",
    response_model=ExecutionRead,
    summary="Explicitly approve an IMPLEMENT scope execution to transition from Pending to Running",
)
async def approve_execution(
    execution_id: uuid.UUID,
    body: ExecutionApproveRequest,
    background_tasks: BackgroundTasks,
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
            detail={"error": "not_found", "message": "Execution record not found.", "status_code": 404},
        )

    # Ownership check: only owner or superuser can approve
    if execution.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Only the task owner can approve this execution.", "status_code": 403},
        )

    if execution.status != ExecutionStatus.Pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "invalid_state",
                "message": f"Execution status must be 'Pending' to approve, currently '{execution.status.value}'.",
                "status_code": 409,
            },
        )

    # Check 10-minute expiry window
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    created_at = execution.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    elapsed_seconds = (now - created_at).total_seconds()
    if elapsed_seconds > 600:  # 10 minutes
        execution.status = ExecutionStatus.Cancelled
        execution.error_message = "Approval window expired (10 minutes limit exceeded)."
        await db.commit()
        await db.refresh(execution)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "approval_expired",
                "message": "Approval window has expired (10 minutes limit). Execution cancelled.",
                "status_code": 400,
            },
        )

    agent_impl = agent_registry.get(execution.agent_slug)
    if not agent_impl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Agent implementation not found in registry.", "status_code": 404},
        )

    task = AgentTask(
        task_id=execution.task_id,
        agent_slug=execution.agent_slug,
        instruction=execution.instruction,
        scope=execution.scope,
        context={"approved": True, "approval_note": body.note},
        requested_by=current_user.id,
    )
    context = ExecutionContext(
        allowed_tools=agent_impl.allowed_tools,
        dry_run=False,
    )

    background_tasks.add_task(
        run_agent_in_background,
        agent_slug=execution.agent_slug,
        task=task,
        context=context,
        execution_id=execution.id,
    )

    return _serialize_execution(execution)


@router.post(
    "/{execution_id}/reject",
    response_model=ExecutionRead,
    summary="Explicitly reject a pending execution and transition to Cancelled",
)
async def reject_execution(
    execution_id: uuid.UUID,
    body: ExecutionRejectRequest,
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
            detail={"error": "not_found", "message": "Execution record not found.", "status_code": 404},
        )

    if execution.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Only the task owner can reject this execution.", "status_code": 403},
        )

    if execution.status != ExecutionStatus.Pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "invalid_state",
                "message": f"Execution status must be 'Pending' to reject, currently '{execution.status.value}'.",
                "status_code": 409,
            },
        )

    execution.status = ExecutionStatus.Cancelled
    execution.error_message = f"Execution rejected by user: {body.reason}"
    await db.commit()
    await db.refresh(execution)
    return _serialize_execution(execution)

