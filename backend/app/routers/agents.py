from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.agents.lifecycle import AgentLifecycleManager
from backend.app.database import get_db
from backend.app.dependencies import get_current_superuser
from backend.app.models.agent import Agent, AgentStatus
from backend.app.models.user import User
from backend.app.schemas.agent import (
    AgentConfigUpdate,
    AgentRead,
    AgentStatusUpdate,
    AgentUpdate,
)

router = APIRouter(prefix="/agents", tags=["Agent Registry"])

PHASE_01_SEED_AGENTS = [
    {
        "slug": "curizx-core",
        "name": "Curizx AI Employee",
        "purpose": "Flagship autonomous customer conversations, inbound sales lead generation, domain business knowledge retrieval, and automated workflow handoffs.",
        "status": AgentStatus.Planned,
        "allowed_tools": ["CRM Sync", "Vector Knowledge Retrieval", "Calendar Booking", "Lead Qualifier"],
        "phase": 1,
        "limitations": ["Requires sandboxed execution environment", "Requires human review on payment transfers"],
    },
    {
        "slug": "rag-engine-v1",
        "name": "Knowledge Architect RAG",
        "purpose": "Zero-hallucination document synthesis pipeline implementing semantic chunking, metadata filtering, and cross-encoder citation verification.",
        "status": AgentStatus.Planned,
        "allowed_tools": ["Chroma/Qdrant Vector DB", "Hierarchical Document Chunker", "Cohere Reranker"],
        "phase": 1,
        "limitations": ["Requires chunk size tuning for scanned OCR docs"],
    },
    {
        "slug": "mcp-host-bridge",
        "name": "MCP Tool Orchestrator",
        "purpose": "Model Context Protocol client and server bridge enabling safe LLM inspection of local files, schemas, and API tool endpoints.",
        "status": AgentStatus.Planned,
        "allowed_tools": ["MCP Filesystem Server", "PostgreSQL Query Server", "GitHub API Protocol Server"],
        "phase": 1,
        "limitations": ["Read-only file permissions by default", "Stdio sandbox timeout of 10s"],
    },
    {
        "slug": "infer-router",
        "name": "Multi-Model Inference Router",
        "purpose": "Dynamic cost and latency model dispatcher routing sub-cent lightweight tasks away from costly frontier reasoning models.",
        "status": AgentStatus.Planned,
        "allowed_tools": ["Token Counter", "Latency Evaluator", "JSON Schema Validator"],
        "phase": 1,
        "limitations": ["Requires upstream provider health checks"],
    },
    {
        "slug": "flow-executor",
        "name": "Workflow Automation Worker",
        "purpose": "Durable event-driven asynchronous background processing daemon for webhook validation and downstream CRM enrichment.",
        "status": AgentStatus.Planned,
        "allowed_tools": ["Webhook Ingestion", "Payload Transformer", "Slack/Email Notifier", "State Store"],
        "phase": 1,
        "limitations": ["Idempotency keys required on mutating webhook calls"],
    },
    {
        "slug": "arch-sentinel",
        "name": "Code & Architecture Auditor",
        "purpose": "Static AST verification, prompt injection scanning, and schema contract audit harness for AI systems.",
        "status": AgentStatus.Planned,
        "allowed_tools": ["AST Parser", "Pydantic/Zod Schema Linter", "Adversarial Prompt Probe"],
        "phase": 1,
        "limitations": ["Heuristic detection may report false positives on custom prompt formats"],
    },
    {
        "slug": "eval-matrix",
        "name": "Eval & Benchmark Harness",
        "purpose": "Systematic regression test suite measuring retrieval faithfulness, answer hallucination rate, and token efficiency.",
        "status": AgentStatus.Planned,
        "allowed_tools": ["Context Relevance Scorer", "Faithfulness Detector", "Answer Relevance Analyzer"],
        "phase": 1,
        "limitations": ["Judge model evaluations incur token costs on large test batches"],
    },
    {
        "slug": "masterclass-synth",
        "name": "Masterclass Content Synthesizer",
        "purpose": "Multi-stage technical curriculum distillation pipeline generating lesson blueprints and architectural diagrams.",
        "status": AgentStatus.Planned,
        "allowed_tools": ["Markdown Formatter", "ASCII Diagram Generator", "YouTube Show-Notes Compiler"],
        "phase": 1,
        "limitations": ["Outputs require human review for accuracy"],
    },
]


@router.get(
    "",
    response_model=List[AgentRead],
    summary="List registered agents (Public endpoint)",
)
async def list_agents(
    status: Optional[AgentStatus] = Query(None, description="Filter by agent status"),
    search: Optional[str] = Query(None, description="Search query in name, slug, or purpose"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Agent)
    if status is not None:
        query = query.where(Agent.status == status)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                Agent.name.ilike(search_pattern),
                Agent.slug.ilike(search_pattern),
                Agent.purpose.ilike(search_pattern),
            )
        )

    query = query.order_by(Agent.phase.asc(), Agent.created_at.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/{slug}",
    response_model=AgentRead,
    summary="Get single agent by slug (Public endpoint)",
)
async def get_agent(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.slug == slug.lower().strip()))
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": f"Agent with slug '{slug}' not found",
                "status_code": 404,
            },
        )
    return agent


@router.patch(
    "/{slug}",
    response_model=AgentRead,
    summary="Update agent specification (Superuser only)",
)
async def update_agent(
    slug: str,
    agent_update: AgentUpdate,
    current_superuser: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.slug == slug.lower().strip()))
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": f"Agent with slug '{slug}' not found",
                "status_code": 404,
            },
        )

    update_data = agent_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)

    await db.commit()
    await db.refresh(agent)
    return agent


@router.post(
    "/seed",
    response_model=List[AgentRead],
    summary="Seed 8 Phase 01 agents into the registry (Superuser only)",
)
async def seed_agents(
    current_superuser: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    seeded = []
    for data in PHASE_01_SEED_AGENTS:
        existing = await db.execute(select(Agent).where(Agent.slug == data["slug"]))
        agent = existing.scalars().first()
        if not agent:
            agent = Agent(**data)
            db.add(agent)
            await db.flush()
        seeded.append(agent)

    await db.commit()
    for a in seeded:
        await db.refresh(a)

    return seeded


@router.patch(
    "/{slug}/status",
    response_model=AgentRead,
    summary="Update agent status enforcing lifecycle state transitions (Superuser only)",
)
async def update_agent_status(
    slug: str,
    status_update: AgentStatusUpdate,
    current_superuser: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.slug == slug.lower().strip()))
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": f"Agent with slug '{slug}' not found",
                "status_code": 404,
            },
        )

    # Validates lifecycle transition rules; raises TransitionError (caught and returned as 422) if invalid
    AgentLifecycleManager.validate_transition(
        current_status=agent.status,
        target_status=status_update.status,
        reason=status_update.reason or "",
    )

    agent.status = status_update.status
    await db.commit()
    await db.refresh(agent)
    return agent


@router.post(
    "/{slug}/configure",
    response_model=AgentRead,
    summary="Configure agent and transition from Planned to Configured (Superuser only)",
)
async def configure_agent(
    slug: str,
    config: AgentConfigUpdate,
    current_superuser: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.slug == slug.lower().strip()))
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "not_found",
                "message": f"Agent with slug '{slug}' not found",
                "status_code": 404,
            },
        )

    # Validates transition to Configured
    AgentLifecycleManager.validate_transition(
        current_status=agent.status,
        target_status=AgentStatus.Configured,
        reason="Agent configured by superuser",
    )

    if config.allowed_tools is not None:
        agent.allowed_tools = config.allowed_tools
    if config.limitations is not None:
        agent.limitations = config.limitations
    if config.purpose is not None:
        agent.purpose = config.purpose

    agent.status = AgentStatus.Configured
    await db.commit()
    await db.refresh(agent)
    return agent
