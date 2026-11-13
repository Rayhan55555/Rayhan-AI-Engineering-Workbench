from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.tools.architecture_analyzer import ArchitectureAnalyzer
from backend.app.tools.diagram_generator import DiagramGenerator, DiagramResult
from backend.app.tools.adr_generator import ADRGenerator, ADRContent, ADRSummary
from backend.app.architecture.evaluator import ArchitectureReport

router = APIRouter(prefix="/architecture", tags=["Architecture Agent"])


class AnalyzeRequest(BaseModel):
    analysis_type: str = Field("full", description="full | layers | dependencies | api | database | security")
    target: Optional[str] = None


class DiagramRequest(BaseModel):
    diagram_type: str = Field("system", description="system | er | api_flow | agent | component")
    target: Optional[str] = None


class CreateADRRequest(BaseModel):
    title: str
    decision: str
    context: str
    status: str = "Accepted"


@router.post("/analyze", response_model=ArchitectureReport)
async def analyze_architecture(
    body: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Runs static AST and runtime architectural analysis:
    - Layer boundary check
    - Circular dependency graph
    - API contract audit
    - Database schema health
    - Overall health score (0-100)
    """
    report = ArchitectureAnalyzer.full_audit(target=body.target)
    return report


@router.post("/diagram", response_model=DiagramResult)
async def generate_diagram(
    body: DiagramRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generates authentic, syntactically valid Mermaid.js diagrams from parsed codebase entities.
    Diagram types: system, er, api_flow, agent, component.
    """
    try:
        result = DiagramGenerator.generate(body.diagram_type, target=body.target)
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )


@router.post("/adr", response_model=ADRContent)
async def create_adr(
    body: CreateADRRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Generates a standard Architecture Decision Record (SUGGEST scope).
    Returned in memory — writing to /docs/adr/ requires IMPLEMENT scope and human approval.
    """
    adr = ADRGenerator.generate(
        title=body.title,
        decision=body.decision,
        context=body.context,
        status=body.status,
    )
    return adr


@router.get("/adrs", response_model=List[ADRSummary])
async def list_existing_adrs(
    current_user: User = Depends(get_current_user),
):
    """
    Scans /docs/adr/ directory and returns list of existing Architecture Decision Records.
    """
    adrs = ADRGenerator.list_existing_adrs()
    return adrs
