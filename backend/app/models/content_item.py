"""ContentItem model for Phase 12 Content Studio lifecycle and calendar management."""

import enum
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import DateTime, ForeignKey, String, Text, func, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from backend.app.database import Base
except ImportError:
    from app.database import Base


class ContentTypeEnum(str, enum.Enum):
    ARTICLE = "article"
    TUTORIAL = "tutorial"
    CASE_STUDY = "case_study"
    YOUTUBE_SCRIPT = "youtube_script"
    SOCIAL_PACK = "social_pack"


class ContentStageEnum(str, enum.Enum):
    IDEA = "idea"
    OUTLINE = "outline"
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"


class ContentChannelEnum(str, enum.Enum):
    BLOG = "blog"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    CROSS_PLATFORM = "cross_platform"


class ContentItem(Base):
    """Editorial content artifact tracked from Idea -> Outline -> Draft -> Approved -> Published."""

    __tablename__ = "content_items"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ContentTypeEnum.ARTICLE.value,
        index=True,
    )
    stage: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ContentStageEnum.IDEA.value,
        index=True,
    )
    channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ContentChannelEnum.BLOG.value,
        index=True,
    )
    body_markdown: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )
    rag_sources: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
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

    author = relationship("User", foreign_keys=[created_by], lazy="selectin")
    reviewer = relationship("User", foreign_keys=[approved_by], lazy="selectin")
