"""Phase 13 database models: PortfolioProject, ContactInquiry, and EvalBenchmarkRun."""

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

try:
    from backend.app.database import Base
except ImportError:
    from app.database import Base


class PortfolioCategoryEnum(str, enum.Enum):
    AI_AGENT = "ai_agent"
    RAG = "rag"
    LLM_APP = "llm_app"
    AUTOMATION = "automation"
    BACKEND = "backend"
    MCP = "mcp"
    SAAS = "saas"


class PortfolioStatusEnum(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class PortfolioProject(Base):
    """
    Publicly showcaseable project record.
    Strict rule: is_public MUST be manually approved (False by default).
    Never exposes private workbench credentials, secrets, or unapproved drafts.
    """

    __tablename__ = "portfolio_projects"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    tagline: Mapped[str] = mapped_column(
        String(500),
        default="",
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    architecture_overview: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    challenges_solutions: Mapped[Optional[List[Dict[str, str]]]] = mapped_column(
        JSON,
        nullable=True,
    )
    tech_stack: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        default=PortfolioCategoryEnum.AI_AGENT.value,
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=PortfolioStatusEnum.IN_PROGRESS.value,
        index=True,
        nullable=False,
    )
    github_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    demo_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    case_study_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("content_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False,
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ContactInquiry(Base):
    """Stores verified public contact inquiries (never exposed on public endpoints)."""

    __tablename__ = "contact_inquiries"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class EvalBenchmarkRun(Base):
    """Persisted benchmark execution metrics from EvalMatrixAgent."""

    __tablename__ = "eval_benchmark_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    benchmark_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    total_tests: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    run_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
