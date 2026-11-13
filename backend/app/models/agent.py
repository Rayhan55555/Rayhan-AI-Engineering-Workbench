import enum
import uuid
from datetime import datetime
from typing import List
from sqlalchemy import DateTime, Enum, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database import Base


class AgentStatus(str, enum.Enum):
    Planned = "Planned"
    Configured = "Configured"
    Available = "Available"
    Running = "Running"
    Failed = "Failed"
    Maintenance = "Maintenance"


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    purpose: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, name="agent_status_enum", native_enum=False),
        default=AgentStatus.Planned,
        nullable=False,
    )
    allowed_tools: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    phase: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    limitations: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
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
