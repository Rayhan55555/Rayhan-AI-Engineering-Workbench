import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from backend.app.database import Base


class ToolAudit(Base):
    """
    Immutable audit log for all tool calls in the workbench.
    Per security policy:
    1. Tool audits are NEVER deleted.
    2. Parameters are scrubbed of secrets before saving.
    """
    __tablename__ = "tool_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_slug = Column(String(100), nullable=True, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    parameters = Column(JSON, nullable=False, default=dict)
    output_summary = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
