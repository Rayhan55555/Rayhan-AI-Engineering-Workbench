from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class ToolCategory(str, Enum):
    GITHUB = "github"
    FILESYSTEM = "filesystem"
    WEB = "web"
    DATABASE = "database"
    SHELL = "shell"


class ToolPermissionScope(str, Enum):
    READ_ONLY = "READ_ONLY"
    SUGGEST = "SUGGEST"
    IMPLEMENT = "IMPLEMENT"
    DEPLOY = "DEPLOY"


class ToolRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolInputSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class ToolDefinition(BaseModel):
    name: str
    description: str
    category: ToolCategory
    permission_scope: ToolPermissionScope
    requires_approval: bool = False
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW
    inputSchema: ToolInputSchema
    enabled: bool = True
    phase_lock_note: Optional[str] = None


class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[Union[str, int]] = None


class MCPError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[MCPError] = None
    id: Optional[Union[str, int]] = None


class ToolCallResult(BaseModel):
    tool_name: str
    success: bool
    content: List[Dict[str, Any]] = Field(default_factory=list)
    output_summary: Optional[str] = None
    error: Optional[str] = None
    requires_approval: bool = False
    approval_id: Optional[str] = None
    preview: Optional[Dict[str, Any]] = None
    duration_ms: int = 0
