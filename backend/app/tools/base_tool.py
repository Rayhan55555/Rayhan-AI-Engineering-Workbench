from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.agents.base_agent import ExecutionContext
from backend.app.agents.permissions import PermissionLevel


class ToolResult(BaseModel):
    success: bool
    output: Any
    error: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    simulated: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    name: str
    description: str
    required_permission: PermissionLevel
    safe_by_default: bool = True

    @abstractmethod
    async def execute(
        self,
        params: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        """Execute the tool operation within security constraints."""
        pass
