from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int = Field(ge=0, description="Total count of matching items")
    page: int = Field(ge=1, description="Current page number")
    limit: int = Field(ge=1, le=50, description="Items per page")
    total_pages: int = Field(ge=0, description="Total pages available")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    status_code: int = Field(..., description="HTTP status code")
