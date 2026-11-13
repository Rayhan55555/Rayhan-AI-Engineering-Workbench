import enum
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession


class TaskScope(str, enum.Enum):
    read_only = "read_only"
    suggest = "suggest"
    implement = "implement"
    deploy = "deploy"


class Artifact(BaseModel):
    name: str
    artifact_type: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    source: str
    snippet: str
    confidence: float = 1.0


class ValidationResult(BaseModel):
    valid: bool
    error: Optional[str] = None


class AgentTask(BaseModel):
    task_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    agent_slug: str
    instruction: str = Field(..., max_length=2000)
    scope: TaskScope = TaskScope.read_only
    context: Dict[str, Any] = Field(default_factory=dict)
    requested_by: uuid.UUID
    approved: bool = False


class AgentResult(BaseModel):
    success: bool
    output: str
    artifacts: List[Artifact] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    simulated: bool = True  # MUST be True if no real execution happened


class ExecutionContext(BaseModel):
    project_id: Optional[uuid.UUID] = None
    allowed_tools: List[str] = Field(default_factory=list)
    max_tokens: int = 4000
    timeout_secs: int = 60
    dry_run: bool = False


class CapabilityDescription(BaseModel):
    slug: str
    name: str
    purpose: str
    phase: int
    version: str
    allowed_tools: List[str]
    required_permissions: List[str]
    limitations: List[str]


class BaseAgent(ABC):
    # Identity
    slug: str
    name: str
    purpose: str
    phase: int = 1
    version: str = "0.1.0"

    # Capabilities
    allowed_tools: List[str] = []
    required_permissions: List[str] = []
    limitations: List[str] = []

    @abstractmethod
    async def validate_input(self, task: AgentTask) -> ValidationResult:
        """Validate instruction length, structure, and scope validity."""
        pass

    @abstractmethod
    async def execute(self, task: AgentTask, context: ExecutionContext) -> AgentResult:
        """Execute the agent task and return structured AgentResult."""
        pass

    @abstractmethod
    async def describe_capabilities(self) -> CapabilityDescription:
        """Describe identity and tool capabilities honestly."""
        pass

    async def run(
        self,
        task: AgentTask,
        context: ExecutionContext,
        db: AsyncSession,
        execution_id: uuid.UUID,
    ):
        """
        Provided execution lifecycle method (not overridable):
        validate -> check permissions -> execute -> record in DB -> return.
        Never swallows errors silently.
        """
        from backend.app.models.agent_execution import (
            AgentExecution,
            ExecutionStatus,
        )
        from backend.app.agents.permissions import check_permission

        start_perf = time.perf_counter()
        now_utc = datetime.now(timezone.utc)

        # Retrieve execution record
        from sqlalchemy import select
        res = await db.execute(
            select(AgentExecution).where(AgentExecution.id == execution_id)
        )
        execution = res.scalars().first()
        if not execution:
            raise ValueError(f"Execution record {execution_id} not found")

        try:
            # 1. Update status to Running
            execution.status = ExecutionStatus.Running
            execution.started_at = now_utc
            await db.commit()

            # 2. Validate input
            val_result = await self.validate_input(task)
            if not val_result.valid:
                execution.status = ExecutionStatus.Failed
                execution.error_message = f"Validation failed: {val_result.error}"
                execution.completed_at = datetime.now(timezone.utc)
                execution.duration_ms = int((time.perf_counter() - start_perf) * 1000)
                await db.commit()
                return execution

            # 3. Check permissions (approved tasks skip default unapproved lock)
            if task.scope == TaskScope.implement and (task.approved or task.context.get("approved")):
                is_permitted, perm_reason = True, "Approved IMPLEMENT execution"
            else:
                # Filter requested tools to those relevant to the current task scope
                scope_tools = [
                    t for t in self.allowed_tools
                    if not (t.lower() == "test_runner" and task.scope != TaskScope.implement)
                ]
                is_permitted, perm_reason = check_permission(
                    agent_slug=self.slug,
                    scope=task.scope,
                    requested_tools=scope_tools,
                )
            if not is_permitted:
                execution.status = ExecutionStatus.Failed
                execution.error_message = f"Permission denied: {perm_reason}"
                execution.completed_at = datetime.now(timezone.utc)
                execution.duration_ms = int((time.perf_counter() - start_perf) * 1000)
                await db.commit()
                return execution

            # 4. Execute concrete agent stub
            result: AgentResult = await self.execute(task, context)

            # 5. Record results
            execution.status = ExecutionStatus.Completed if result.success else ExecutionStatus.Failed
            execution.output = result.output
            execution.simulated = result.simulated
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_ms = int((time.perf_counter() - start_perf) * 1000)
            if not result.success:
                execution.error_message = "Agent execution did not succeed"

            await db.commit()
            return execution

        except Exception as exc:
            # Never swallow errors silently
            execution.status = ExecutionStatus.Failed
            execution.error_message = f"Runtime exception: {str(exc)}"
            execution.completed_at = datetime.now(timezone.utc)
            execution.duration_ms = int((time.perf_counter() - start_perf) * 1000)
            await db.commit()
            raise exc
