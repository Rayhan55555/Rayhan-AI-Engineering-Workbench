import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from backend.app.database import Base


class ToolApproval(Base):
    """
    Approval requests for tools requiring human-in-the-loop validation
    (e.g., file writes, delete operations, PR comments, issue creation, shell test runs).
    Approvals expire after 10 minutes by default.
    """
    __tablename__ = "tool_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_slug = Column(String(100), nullable=True, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    parameters = Column(JSON, nullable=False, default=dict)
    preview = Column(JSON, nullable=False, default=dict)  # diff summary, target path, command, etc.
    risk_level = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, approved, rejected, expired
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        if self.expires_at:
            # handle timezone aware/naive
            exp = self.expires_at if self.expires_at.tzinfo else self.expires_at.replace(tzinfo=timezone.utc)
            return now > exp
        return False
