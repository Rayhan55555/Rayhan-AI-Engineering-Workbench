import uuid as _uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.models.tool_approval import ToolApproval
from backend.app.mcp.protocol import ToolRiskLevel


DEFAULT_EXPIRY_MINUTES = 10


class ApprovalManager:
    """
    Manages human approval lifecycle for write and destructive tools.
    Enforces 10-minute expiry, risk-level assignments, and execution gating.
    """

    @classmethod
    def _coerce_uuid(cls, val: Any) -> Any:
        if isinstance(val, str):
            try:
                return _uuid.UUID(val)
            except ValueError:
                return val
        return val

    @classmethod
    async def create_request(
        cls,
        db: AsyncSession,
        user_id: Any,
        tool_name: str,
        parameters: Dict[str, Any],
        preview: Dict[str, Any],
        risk_level: str = "medium",
        agent_slug: Optional[str] = None,
        expiry_minutes: int = DEFAULT_EXPIRY_MINUTES,
    ) -> ToolApproval:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=expiry_minutes)
        uid = cls._coerce_uuid(user_id)

        approval = ToolApproval(
            user_id=uid,
            agent_slug=agent_slug,
            tool_name=tool_name,
            parameters=parameters,
            preview=preview,
            risk_level=risk_level,
            status="pending",
            expires_at=expires_at,
        )

        db.add(approval)
        await db.commit()
        await db.refresh(approval)
        return approval

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        approval_id: Any,
        user_id: Any,
    ) -> Optional[ToolApproval]:
        aid = cls._coerce_uuid(approval_id)
        uid = cls._coerce_uuid(user_id)
        stmt = select(ToolApproval).where(
            ToolApproval.id == aid,
            ToolApproval.user_id == uid,
        )
        result = await db.execute(stmt)
        return result.scalars().first()


    @classmethod
    async def list_pending(
        cls,
        db: AsyncSession,
        user_id: Any,
    ) -> List[ToolApproval]:
        uid = cls._coerce_uuid(user_id)
        stmt = select(ToolApproval).where(
            ToolApproval.user_id == uid,
            ToolApproval.status == "pending",
        ).order_by(desc(ToolApproval.created_at))


        result = await db.execute(stmt)
        approvals = list(result.scalars().all())

        # Update expired items on the fly
        active = []
        now = datetime.now(timezone.utc)
        has_expired = False
        for app in approvals:
            exp = app.expires_at if app.expires_at.tzinfo else app.expires_at.replace(tzinfo=timezone.utc)
            if now > exp:
                app.status = "expired"
                has_expired = True
            else:
                active.append(app)

        if has_expired:
            await db.commit()

        return active

    @classmethod
    async def approve(
        cls,
        db: AsyncSession,
        approval_id: Any,
        user_id: Any,
    ) -> ToolApproval:
        approval = await cls.get_by_id(db, approval_id, user_id)
        if not approval:
            raise ValueError("Approval request not found.")
        if approval.status != "pending":
            raise ValueError(f"Approval is already {approval.status}.")
        if approval.is_expired():
            approval.status = "expired"
            await db.commit()
            raise ValueError("Approval request has expired (10-minute window exceeded).")

        approval.status = "approved"
        approval.resolved_at = datetime.now(timezone.utc)
        approval.resolved_by = user_id
        await db.commit()
        await db.refresh(approval)
        return approval

    @classmethod
    async def reject(
        cls,
        db: AsyncSession,
        approval_id: Any,
        user_id: Any,
        reason: Optional[str] = None,
    ) -> ToolApproval:
        approval = await cls.get_by_id(db, approval_id, user_id)
        if not approval:
            raise ValueError("Approval request not found.")
        if approval.status != "pending":
            raise ValueError(f"Approval is already {approval.status}.")

        approval.status = "rejected"
        approval.rejection_reason = reason or "Rejected by user."
        approval.resolved_at = datetime.now(timezone.utc)
        approval.resolved_by = user_id
        await db.commit()
        await db.refresh(approval)
        return approval
