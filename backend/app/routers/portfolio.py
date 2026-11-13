"""Public Portfolio & Safe Demos API Router (Phase 13).

CRITICAL BOUNDARY RULES:
- Public endpoints NEVER expose private workbench data, credentials, tokens,
  unapproved drafts, agent execution logs, database internals, or user PII.
- Projects on public routes strictly require is_public == True (manual superuser publish only).
- Articles and Case Studies on public routes strictly require stage == 'published'.
- Safe Demos execute read-only in-memory tooling with zero filesystem access and zero DB persistence.
"""

import asyncio
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.base_agent import ExecutionContext
from backend.app.database import get_db
from backend.app.dependencies import get_current_superuser, get_current_user
from backend.app.models.content_item import ContentItem, ContentStageEnum, ContentTypeEnum
from backend.app.models.portfolio_project import (
    ContactInquiry,
    PortfolioCategoryEnum,
    PortfolioProject,
    PortfolioStatusEnum,
)
from backend.app.models.user import User
from backend.app.tools.code_analyzer import CodeAnalyzerTool
from backend.app.tools.diagram_generator import DiagramGenerator
from backend.app.tools.security_scanner import SecurityScannerTool

router = APIRouter(prefix="/portfolio", tags=["Public Portfolio"])


# ----------------------------------------------------------------------
# Safe Public Schemas (Never include internal user IDs / audit secrets)
# ----------------------------------------------------------------------

class PortfolioSocialLinks(BaseModel):
    github: str
    linkedin: str
    youtube: str


class PublicProfileResponse(BaseModel):
    name: str
    title: str
    tagline: str
    bio: str
    location: str
    collaboration_status: str
    expertise: List[str]
    tech_badges: List[str]
    social_links: PortfolioSocialLinks


class PublicProject(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    tagline: str
    description: str
    architecture_overview: str
    challenges_solutions: List[Dict[str, str]] = Field(default_factory=list)
    tech_stack: List[str]
    category: str
    status: str
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    case_study_slug: Optional[str] = None
    is_featured: bool
    is_public: bool
    sort_order: int
    published_at: Optional[datetime] = None

    @field_validator("challenges_solutions", mode="before")
    @classmethod
    def coerce_challenges(cls, v: Any) -> List[Dict[str, str]]:
        return list(v) if v else []

    model_config = ConfigDict(from_attributes=True)


class PublicArticle(BaseModel):
    slug: str
    title: str
    content_type: str
    summary: str
    body_markdown: str
    reading_time_min: int
    word_count: int
    published_at: Optional[datetime] = None


class PublicCaseStudy(BaseModel):
    slug: str
    title: str
    summary: str
    body_markdown: str
    benchmark_flags: List[str] = Field(default_factory=list)
    reading_time_min: int
    published_at: Optional[datetime] = None


class DemoSamplePreset(BaseModel):
    label: str
    language: str
    input_code: str


class SafeDemoDefinition(BaseModel):
    slug: str
    title: str
    description: str
    demo_label: str = "Demo — Sample Data"
    read_only: bool = True
    rate_limit: str = "10 requests / minute per IP"
    timeout_seconds: int = 30
    persisted: bool = False
    samples: List[DemoSamplePreset]


class DemoRunRequest(BaseModel):
    code: Optional[str] = Field(None, max_length=8000)
    prompt: Optional[str] = Field(None, max_length=2000)
    language: Literal["python", "typescript"] = "python"


class DemoRunResponse(BaseModel):
    slug: str
    demo_label: str = "Demo — Sample Data"
    sample_data_only: bool = True
    persisted: bool = False
    execution_ms: int
    output: Dict[str, Any]


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    subject: str = Field(..., min_length=3, max_length=200)
    message: str = Field(..., min_length=5, max_length=1000)
    honeypot: Optional[str] = Field(default="", max_length=200)
    website: Optional[str] = Field(default="", max_length=200)

    @field_validator("name", "subject", "message", mode="before")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


class ContactResponse(BaseModel):
    received: bool
    message: str


# ----------------------------------------------------------------------
# Private Management Schemas (Auth Required)
# ----------------------------------------------------------------------

class ProjectManageCreate(BaseModel):
    slug: Optional[str] = Field(None, max_length=255)
    title: str = Field(..., min_length=3, max_length=255)
    tagline: str = Field(..., min_length=3, max_length=500)
    description: str = Field(..., min_length=10)
    architecture_overview: str = ""
    challenges_solutions: List[Dict[str, str]] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    category: Literal["ai_agent", "rag", "llm_app", "automation", "backend", "mcp", "saas"] = "ai_agent"
    status: Literal["in_progress", "completed", "archived"] = "in_progress"
    github_url: Optional[str] = Field(None, max_length=500)
    demo_url: Optional[str] = Field(None, max_length=500)
    case_study_id: Optional[uuid.UUID] = None
    is_featured: bool = False
    sort_order: int = 0


class ProjectManageUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    tagline: Optional[str] = Field(None, min_length=3, max_length=500)
    description: Optional[str] = None
    architecture_overview: Optional[str] = None
    challenges_solutions: Optional[List[Dict[str, str]]] = None
    tech_stack: Optional[List[str]] = None
    category: Optional[Literal["ai_agent", "rag", "llm_app", "automation", "backend", "mcp", "saas"]] = None
    status: Optional[Literal["in_progress", "completed", "archived"]] = None
    github_url: Optional[str] = Field(None, max_length=500)
    demo_url: Optional[str] = Field(None, max_length=500)
    case_study_id: Optional[uuid.UUID] = None
    is_featured: Optional[bool] = None
    sort_order: Optional[int] = None


# ----------------------------------------------------------------------
# Safe Demo Registry (Strictly isolated, sample presets only)
# ----------------------------------------------------------------------

SAFE_DEMOS: List[SafeDemoDefinition] = [
    SafeDemoDefinition(
        slug="code-analyzer",
        title="Code Analyzer Demo",
        description="Inspect Python or TypeScript source snippets via AST complexity, import hygiene, and type coverage checks.",
        samples=[
            DemoSamplePreset(
                label="Async Service Handler (Sample)",
                language="python",
                input_code=(
                    "import os\nimport json\n\n"
                    "def process_records(items, threshold):\n"
                    "    matched = []\n"
                    "    for item in items:\n"
                    "        if item.get('score', 0) >= threshold:\n"
                    "            if item.get('active'):\n"
                    "                matched.append(item)\n"
                    "    return matched\n"
                ),
            ),
            DemoSamplePreset(
                label="Typed Utility Function (Sample)",
                language="python",
                input_code=(
                    "def compute_ratio(passed: int, total: int) -> float:\n"
                    "    \"\"\"Compute safe pass percentage ratio.\"\"\"\n"
                    "    if total <= 0:\n"
                    "        return 0.0\n"
                    "    return round((passed / total) * 100.0, 2)\n"
                ),
            ),
        ],
    ),
    SafeDemoDefinition(
        slug="security-scanner",
        title="Security Scanner Demo",
        description="Scan pasted code snippets for CWE patterns including SQL string formatting, command injection, and secret exposure.",
        samples=[
            DemoSamplePreset(
                label="SQL & Shell Anti-Pattern (Sample)",
                language="python",
                input_code=(
                    "import subprocess\n\n"
                    "def fetch_user_unsafe(cursor, user_id, export_cmd):\n"
                    "    cursor.execute(f\"SELECT * FROM accounts WHERE id = {user_id}\")\n"
                    "    subprocess.run(export_cmd, shell=True)\n"
                ),
            ),
            DemoSamplePreset(
                label="Parameterized Query Baseline (Sample)",
                language="python",
                input_code=(
                    "from sqlalchemy import select\n\n"
                    "async def fetch_public_project(session, slug: str):\n"
                    "    stmt = select(PortfolioProject).where(PortfolioProject.slug == slug)\n"
                    "    return await session.execute(stmt)\n"
                ),
            ),
        ],
    ),
    SafeDemoDefinition(
        slug="architecture-diagram",
        title="Architecture Diagram Demo",
        description="Synthesize valid Mermaid.js architecture topology graphs from system component descriptions.",
        samples=[
            DemoSamplePreset(
                label="Hybrid RAG + Agent Gateway (Sample)",
                language="python",
                input_code="FastAPI gateway with JWT auth, pgvector hybrid RAG retriever, Redis cache, and Gemini/Claude fallback router",
            ),
            DemoSamplePreset(
                label="Event-Driven SaaS Pipeline (Sample)",
                language="python",
                input_code="Next.js client, Webhook ingestion API, Celery worker queue, PostgreSQL store, and MCP tool server",
            ),
        ],
    ),
]


def _slugify(value: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-") or "project"
    return base[:120]


def _synthesize_sample_mermaid(prompt_text: str) -> Dict[str, Any]:
    """Generates a deterministic Mermaid diagram purely from user prompt keywords (read-only, zero FS access)."""
    desc = (prompt_text or "").strip()
    lower = desc.lower()

    nodes: List[tuple[str, str]] = [("Client", "Client UI / API Consumer")]
    edges: List[str] = []

    if any(k in lower for k in ("gateway", "fastapi", "api", "rest", "backend")):
        nodes.append(("Gateway", "FastAPI REST Gateway"))
        edges.append("Client --> Gateway")
    else:
        nodes.append(("Gateway", "Application API Tier"))
        edges.append("Client --> Gateway")

    if any(k in lower for k in ("auth", "jwt", "rbac", "rate", "security")):
        nodes.append(("Guard", "Auth & Rate-Limit Boundary"))
        edges.append("Gateway --> Guard")
        anchor = "Guard"
    else:
        anchor = "Gateway"

    if any(k in lower for k in ("rag", "vector", "pgvector", "retrieval", "knowledge")):
        nodes.append(("RAG", "Hybrid RAG & Reranker"))
        edges.append(f"{anchor} --> RAG")

    if any(k in lower for k in ("agent", "mcp", "tool", "orchestr", "workflow")):
        nodes.append(("Agent", "Agent Runtime & MCP Tools"))
        edges.append(f"{anchor} --> Agent")

    if any(k in lower for k in ("gemini", "claude", "llm", "model", "router")):
        nodes.append(("LLM", "Multi-Model Router (Gemini / Claude)"))
        edges.append(f"{anchor} --> LLM")

    if any(k in lower for k in ("queue", "worker", "celery", "webhook", "async")):
        nodes.append(("Worker", "Async Worker Queue"))
        edges.append(f"{anchor} --> Worker")

    if any(k in lower for k in ("postgres", "db", "database", "sql", "redis", "cache", "store")):
        nodes.append(("DB", "PostgreSQL / Vector Store"))
        if any(n[0] == "RAG" for n in nodes):
            edges.append("RAG --> DB")
        else:
            edges.append(f"{anchor} --> DB")
    else:
        nodes.append(("DB", "Primary Persistence Tier"))
        edges.append(f"{anchor} --> DB")

    lines = ["graph TD"]
    for nid, label in nodes:
        safe_label = label.replace("[", "(").replace("]", ")")
        lines.append(f"  {nid}[{safe_label}]")
    lines.extend([f"  {e}" for e in edges])
    mermaid_code = "\n".join(lines)
    valid = DiagramGenerator.validate_mermaid_syntax(mermaid_code)

    return {
        "diagram_type": "system_flowchart",
        "mermaid_code": mermaid_code,
        "syntax_valid": valid,
        "components_detected": [label for _, label in nodes],
    }


# ----------------------------------------------------------------------
# PUBLIC ENDPOINTS (Zero Auth Required, Strict Boundary Rules)
# ----------------------------------------------------------------------

@router.get("/profile", response_model=PublicProfileResponse)
async def get_public_profile():
    """Returns curated public engineer profile only (never exposes private details or tokens)."""
    return PublicProfileResponse(
        name="Rayhan",
        title="Applied AI Systems Architect & Engineer",
        tagline="Architecting Intelligence. Engineering the Future.",
        bio=(
            "Applied AI Systems Architect designing production agent runtimes, hybrid vector RAG "
            "pipelines, Model Context Protocol integrations, and multi-model backends grounded in software engineering rigor."
        ),
        location="Bangladesh",
        collaboration_status="Open to global engineering roles & architectural advisory",
        expertise=[
            "AI Systems Architecture",
            "Applied AI Engineering",
            "LLM & RAG Applications",
            "AI Agents & Automation",
            "MCP & Tool Integration",
            "Backend APIs & Databases",
        ],
        tech_badges=[
            "FastAPI",
            "Python / TypeScript",
            "PostgreSQL + pgvector",
            "Model Context Protocol",
            "Gemini & Claude APIs",
            "React + Tailwind CSS",
        ],
        social_links=PortfolioSocialLinks(
            github="https://github.com/rayhan-ai-architect",
            linkedin="https://www.linkedin.com/in/rayhan-badsha-a71662294",
            youtube="https://youtube.com/playlist?list=PLbIePX5F-An4",
        ),
    )


@router.get("/projects", response_model=List[PublicProject])
async def list_public_projects(
    category: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Lists manually published projects ONLY (is_public == True strictly enforced)."""
    stmt = (
        select(PortfolioProject)
        .where(PortfolioProject.is_public == True)
        .order_by(
            desc(PortfolioProject.is_featured),
            PortfolioProject.sort_order.asc(),
            desc(PortfolioProject.created_at),
        )
    )
    if category:
        stmt = stmt.where(PortfolioProject.category == category.strip().lower())
    if featured is not None:
        stmt = stmt.where(PortfolioProject.is_featured == featured)

    res = await db.execute(stmt)
    projects = list(res.scalars().all())

    # Resolve any linked published case study slugs safely
    cs_ids = [p.case_study_id for p in projects if p.case_study_id is not None]
    slug_map: Dict[uuid.UUID, str] = {}
    if cs_ids:
        cs_res = await db.execute(
            select(ContentItem.id, ContentItem.slug).where(
                and_(
                    ContentItem.id.in_(cs_ids),
                    ContentItem.stage == ContentStageEnum.PUBLISHED.value,
                )
            )
        )
        slug_map = {row[0]: row[1] for row in cs_res.all()}

    out: List[PublicProject] = []
    for p in projects:
        dto = PublicProject.model_validate(p)
        if p.case_study_id and p.case_study_id in slug_map:
            dto.case_study_slug = slug_map[p.case_study_id]
        out.append(dto)
    return out


@router.get("/projects/{slug}", response_model=PublicProject)
async def get_public_project_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns a single published project (returns 404 if private or absent)."""
    res = await db.execute(
        select(PortfolioProject).where(
            and_(
                PortfolioProject.slug == slug,
                PortfolioProject.is_public == True,
            )
        )
    )
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Public project not found."},
        )

    dto = PublicProject.model_validate(project)
    if project.case_study_id:
        cs_res = await db.execute(
            select(ContentItem.slug).where(
                and_(
                    ContentItem.id == project.case_study_id,
                    ContentItem.stage == ContentStageEnum.PUBLISHED.value,
                )
            )
        )
        dto.case_study_slug = cs_res.scalar_one_or_none()
    return dto


@router.get("/case-studies", response_model=List[PublicCaseStudy])
async def list_public_case_studies(db: AsyncSession = Depends(get_db)):
    """Lists approved & published Phase 12 case studies ONLY."""
    stmt = (
        select(ContentItem)
        .where(
            and_(
                ContentItem.content_type == ContentTypeEnum.CASE_STUDY.value,
                ContentItem.stage == ContentStageEnum.PUBLISHED.value,
                ContentItem.approved_at.isnot(None),
            )
        )
        .order_by(desc(ContentItem.published_at), desc(ContentItem.created_at))
    )
    res = await db.execute(stmt)
    items = list(res.scalars().all())
    return [
        PublicCaseStudy(
            slug=it.slug,
            title=it.title,
            summary=it.summary,
            body_markdown=it.body_markdown,
            benchmark_flags=list((it.metadata_json or {}).get("benchmark_flags", [])),
            reading_time_min=int((it.metadata_json or {}).get("reading_time_min", 4)),
            published_at=it.published_at,
        )
        for it in items
    ]


@router.get("/case-studies/{slug}", response_model=PublicCaseStudy)
async def get_public_case_study_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ContentItem).where(
        and_(
            ContentItem.slug == slug,
            ContentItem.content_type == ContentTypeEnum.CASE_STUDY.value,
            ContentItem.stage == ContentStageEnum.PUBLISHED.value,
            ContentItem.approved_at.isnot(None),
        )
    )
    res = await db.execute(stmt)
    it = res.scalar_one_or_none()
    if not it:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Published case study not found."},
        )
    return PublicCaseStudy(
        slug=it.slug,
        title=it.title,
        summary=it.summary,
        body_markdown=it.body_markdown,
        benchmark_flags=list((it.metadata_json or {}).get("benchmark_flags", [])),
        reading_time_min=int((it.metadata_json or {}).get("reading_time_min", 4)),
        published_at=it.published_at,
    )


@router.get("/articles", response_model=List[PublicArticle])
async def list_public_articles(db: AsyncSession = Depends(get_db)):
    """Lists published articles & tutorials from Phase 12 content library ONLY."""
    stmt = (
        select(ContentItem)
        .where(
            and_(
                ContentItem.stage == ContentStageEnum.PUBLISHED.value,
                ContentItem.content_type.in_(
                    [ContentTypeEnum.ARTICLE.value, ContentTypeEnum.TUTORIAL.value]
                ),
            )
        )
        .order_by(desc(ContentItem.published_at), desc(ContentItem.created_at))
    )
    res = await db.execute(stmt)
    items = list(res.scalars().all())
    return [
        PublicArticle(
            slug=it.slug,
            title=it.title,
            content_type=it.content_type,
            summary=it.summary,
            body_markdown=it.body_markdown,
            reading_time_min=int((it.metadata_json or {}).get("reading_time_min", 5)),
            word_count=int((it.metadata_json or {}).get("word_count", 0)),
            published_at=it.published_at,
        )
        for it in items
    ]


@router.get("/articles/{slug}", response_model=PublicArticle)
async def get_public_article_by_slug(slug: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ContentItem).where(
        and_(
            ContentItem.slug == slug,
            ContentItem.stage == ContentStageEnum.PUBLISHED.value,
            ContentItem.content_type.in_(
                [ContentTypeEnum.ARTICLE.value, ContentTypeEnum.TUTORIAL.value]
            ),
        )
    )
    res = await db.execute(stmt)
    it = res.scalar_one_or_none()
    if not it:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Published article not found."},
        )
    return PublicArticle(
        slug=it.slug,
        title=it.title,
        content_type=it.content_type,
        summary=it.summary,
        body_markdown=it.body_markdown,
        reading_time_min=int((it.metadata_json or {}).get("reading_time_min", 5)),
        word_count=int((it.metadata_json or {}).get("word_count", 0)),
        published_at=it.published_at,
    )


@router.get("/demos", response_model=List[SafeDemoDefinition])
async def list_safe_demos():
    """Returns catalog of isolated read-only sample demos."""
    return SAFE_DEMOS


@router.post("/demos/{slug}/run", response_model=DemoRunResponse)
async def run_safe_demo(slug: str, body: DemoRunRequest):
    """
    Executes a strictly isolated, read-only sample demo in-memory:
    - Zero filesystem access, zero authentication, zero DB persistence
    - Enforces 30-second execution timeout
    - Rate-limited at 10 req/min per IP
    """
    demo = next((d for d in SAFE_DEMOS if d.slug == slug), None)
    if not demo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Safe demo '{slug}' not found."},
        )

    start = asyncio.get_running_loop().time()

    async def _exec() -> Dict[str, Any]:
        if slug == "code-analyzer":
            sample_code = (body.code or demo.samples[0].input_code).strip()
            tool = CodeAnalyzerTool()
            ctx = ExecutionContext(allowed_tools=["code_analyzer"], dry_run=True)
            res = await tool.execute({"content": sample_code, "language": body.language}, ctx)
            return res.output if res.success else {"error": res.error}

        if slug == "security-scanner":
            sample_code = (body.code or demo.samples[0].input_code).strip()
            scanner = SecurityScannerTool()
            findings = scanner.scan_file_content(sample_code, file_label="demo_sample.py")
            return {
                "total_findings": len(findings),
                "findings": [f.model_dump() for f in findings],
                "scanned_scope": "in-memory sample buffer only",
            }

        # architecture-diagram
        sample_prompt = (body.prompt or body.code or demo.samples[0].input_code).strip()
        return _synthesize_sample_mermaid(sample_prompt)

    try:
        output = await asyncio.wait_for(_exec(), timeout=30.0)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"error": "demo_timeout", "message": "Demo execution exceeded 30s timeout."},
        )

    elapsed_ms = int((asyncio.get_running_loop().time() - start) * 1000)
    return DemoRunResponse(
        slug=slug,
        demo_label="Demo — Sample Data",
        sample_data_only=True,
        persisted=False,
        execution_ms=elapsed_ms,
        output=output,
    )


@router.post("/contact", response_model=ContactResponse)
async def submit_contact_inquiry(
    req: ContactRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Receives public contact inquiries:
    - Enforces 3/hour per IP sliding window via RateLimitMiddleware
    - Rejects automated submissions triggering hidden honeypot fields
    - Logs inquiry cleanly to DB (zero auto-email sent)
    """
    if (req.honeypot and req.honeypot.strip()) or (req.website and req.website.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "spam_detected", "message": "Automated form submission rejected."},
        )

    forwarded = request.headers.get("x-forwarded-for")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")

    inquiry = ContactInquiry(
        id=uuid.uuid4(),
        name=req.name,
        email=str(req.email),
        subject=req.subject,
        message=req.message,
        source_ip=client_ip[:64],
    )
    db.add(inquiry)
    await db.commit()
    return ContactResponse(received=True, message="Message received.")


# ----------------------------------------------------------------------
# PRIVATE MANAGEMENT ENDPOINTS (Auth / Superuser Required)
# ----------------------------------------------------------------------

@router.post("/projects", response_model=PublicProject, status_code=status.HTTP_201_CREATED)
async def create_portfolio_project(
    req: ProjectManageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates a portfolio project privately (is_public=False forced until superuser publishes)."""
    raw_slug = _slugify(req.slug or req.title)
    existing = await db.execute(select(PortfolioProject).where(PortfolioProject.slug == raw_slug))
    if existing.scalar_one_or_none():
        raw_slug = f"{raw_slug}-{uuid.uuid4().hex[:6]}"

    project = PortfolioProject(
        id=uuid.uuid4(),
        slug=raw_slug,
        title=req.title,
        tagline=req.tagline,
        description=req.description,
        architecture_overview=req.architecture_overview,
        challenges_solutions=req.challenges_solutions,
        tech_stack=req.tech_stack,
        category=req.category,
        status=req.status,
        github_url=req.github_url,
        demo_url=req.demo_url,
        case_study_id=req.case_study_id,
        is_featured=req.is_featured,
        is_public=False,  # Always starts private; manual approval required
        sort_order=req.sort_order,
        created_by=current_user.id,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return PublicProject.model_validate(project)


@router.patch("/projects/{project_id}", response_model=PublicProject)
async def update_portfolio_project(
    project_id: uuid.UUID,
    req: ProjectManageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates portfolio project fields (cannot bypass publish approval gate)."""
    res = await db.execute(select(PortfolioProject).where(PortfolioProject.id == project_id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Project {project_id} not found."},
        )

    if project.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "You do not have permission to modify this portfolio project."},
        )

    updates = req.model_dump(exclude_unset=True)
    for key, val in updates.items():
        setattr(project, key, val)

    await db.commit()
    await db.refresh(project)
    return PublicProject.model_validate(project)


@router.patch("/projects/{project_id}/publish", response_model=PublicProject)
async def publish_portfolio_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser),
):
    """Manual superuser approval endpoint: sets is_public = True and stamps published_at."""
    res = await db.execute(select(PortfolioProject).where(PortfolioProject.id == project_id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": f"Project {project_id} not found."},
        )

    project.is_public = True
    project.published_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(project)
    return PublicProject.model_validate(project)
