import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database import Base


class KnowledgeQuery(Base):
    __tablename__ = "knowledge_queries"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    retrieved_chunks: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    top_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    agent_slug: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    response_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    duration_ms: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
