import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.agents.base_agent import TaskScope
from backend.app.models.agent_execution import ExecutionStatus


class ExecutionCreate(BaseModel):
    agent_slug: str = Field(..., min_length=2, max_length=100)
    instruction: str = Field(..., min_length=3, max_length=2000)
    scope: TaskScope = Field(default=TaskScope.read_only)
    project_id: Optional[uuid.UUID] = None
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ExecutionCreateResponse(BaseModel):
    execution_id: uuid.UUID
    task_id: uuid.UUID
    agent_slug: str
    status: ExecutionStatus
    simulated: bool = True
    message: str = "Task accepted and enqueued for background lifecycle execution"


class ExecutionRead(BaseModel):
    id: uuid.UUID
    agent_slug: str
    task_id: uuid.UUID
    user_id: uuid.UUID
    status: ExecutionStatus
    scope: TaskScope
    instruction: str
    output: Optional[str] = None
    error_message: Optional[str] = None
    simulated: bool = True
    tokens_used: Optional[int] = None
    duration_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    bn_report: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ExecutionApproveRequest(BaseModel):
    approved: bool = Field(True, description="Approval confirmation")
    note: Optional[str] = Field(None, max_length=500, description="Optional approval notes")


class ExecutionRejectRequest(BaseModel):
    reason: str = Field(..., min_length=2, max_length=500, description="Reason for rejecting the execution")

