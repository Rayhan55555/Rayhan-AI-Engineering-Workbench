import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.models.agent import AgentStatus


class AgentBase(BaseModel):
    slug: str = Field(..., min_length=2, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    purpose: str = Field(..., min_length=5)
    status: AgentStatus = AgentStatus.Planned
    allowed_tools: List[str] = Field(default_factory=list)
    phase: int = Field(default=1, ge=1)
    limitations: List[str] = Field(default_factory=list)


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    purpose: Optional[str] = Field(None, min_length=5)
    status: Optional[AgentStatus] = None
    allowed_tools: Optional[List[str]] = None
    phase: Optional[int] = Field(None, ge=1)
    limitations: Optional[List[str]] = None


class AgentStatusUpdate(BaseModel):
    status: AgentStatus
    reason: Optional[str] = Field(default="", max_length=500)


class AgentConfigUpdate(BaseModel):
    allowed_tools: Optional[List[str]] = None
    limitations: Optional[List[str]] = None
    purpose: Optional[str] = Field(None, min_length=5)


class AgentRead(AgentBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
