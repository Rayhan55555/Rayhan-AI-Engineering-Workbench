"""Deployment model for tracking release lifecycles and rollback history."""

import enum
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from backend.app.database import Base
except ImportError:
    from app.database import Base


class EnvironmentEnum(str, enum.Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class Deployment(Base):
    """Release record tracking environment, commit, approval, checklist, and rollback lineage."""

    __tablename__ = "deployments"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    environment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="staging",
        index=True,
    )
    version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=DeploymentStatusEnum.PENDING.value,
        index=True,
    )
    triggered_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    checklist_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    rollback_of: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("deployments.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    # Relationships
    user_triggered = relationship("User", foreign_keys=[triggered_by], lazy="selectin")
    user_approved = relationship("User", foreign_keys=[approved_by], lazy="selectin")
    rollback_target = relationship("Deployment", remote_side=[id], lazy="selectin")
