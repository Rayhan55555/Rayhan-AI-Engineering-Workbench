from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.tools.doc_generator import DocGenerator, GeneratedDoc, DocAuditReport

router = APIRouter(prefix="/docs", tags=["Documentation Agent"])


class GenerateDocRequest(BaseModel):
    doc_type: str = Field("api", description="api | readme | setup | changelog")
    target: Optional[str] = None


@router.post("/generate", response_model=GeneratedDoc)
async def generate_document(
    body: GenerateDocRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generates living markdown documentation:
    - API reference manual
    - Project README
    - Setup & Deployment guide
    - Changelog (Keep a Changelog format)
    (SUGGEST scope — writing to disk requires IMPLEMENT authorization).
    """
    try:
        doc = DocGenerator.generate(body.doc_type, target=body.target)
        return doc
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )


@router.post("/audit", response_model=DocAuditReport)
async def audit_documentation(
    current_user: User = Depends(get_current_user),
):
    """
    Audits documentation completeness across API endpoints.
    Identifies undocumented endpoints and generates an overall quality score.
    """
    report = DocGenerator.audit_documentation()
    return report


@router.get("/coverage", response_model=DocAuditReport)
async def get_documentation_coverage(
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves documentation coverage metrics for dashboard presentation.
    """
    report = DocGenerator.audit_documentation()
    return report
