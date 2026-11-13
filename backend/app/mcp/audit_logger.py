import re
import json
import uuid as _uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.app.models.tool_audit import ToolAudit



SENSITIVE_KEY_PATTERNS = [
    re.compile(r"(?i)(password|secret|token|api_key|access_key|auth|bearer|private_key)"),
]

SENSITIVE_VALUE_REGEXES = [
    (re.compile(r"AIza[0-9A-Za-z\-_]{30,}"), "[REDACTED_GEMINI_KEY]"),
    (re.compile(r"sk-ant-[0-9A-Za-z\-_]{20,}"), "[REDACTED_CLAUDE_KEY]"),
    (re.compile(r"ghp_[0-9A-Za-z]{36}"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"github_pat_[0-9A-Za-z_]{50,}"), "[REDACTED_GITHUB_PAT]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_\.=]+"), "Bearer [REDACTED_TOKEN]"),
]


class AuditLogger:
    """
    Immutable audit logging engine for all MCP and tool executions.
    Guarantees:
    - Never deletes records.
    - Masks secret credentials in input parameters.
    - Records latency, status, output summaries, and user attribution.
    """

    @staticmethod
    def sanitize(obj: Any) -> Any:
        if isinstance(obj, dict):
            sanitized = {}
            for k, v in obj.items():
                if any(pat.search(k) for pat in SENSITIVE_KEY_PATTERNS):
                    sanitized[k] = "[REDACTED_CREDENTIAL]"
                else:
                    sanitized[k] = AuditLogger.sanitize(v)
            return sanitized
        elif isinstance(obj, list):
            return [AuditLogger.sanitize(item) for item in obj]
        elif isinstance(obj, str):
            val = obj
            for reg, repl in SENSITIVE_VALUE_REGEXES:
                val = reg.sub(repl, val)
            return val
        return obj

    @staticmethod
    def _coerce_uuid(val: Any) -> Any:
        if isinstance(val, str):
            try:
                return _uuid.UUID(val)
            except ValueError:
                return val
        return val

    @classmethod
    async def log_call(
        cls,
        db: AsyncSession,
        user_id: Any,
        tool_name: str,
        parameters: Dict[str, Any],
        output_summary: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: int = 0,
        agent_slug: Optional[str] = None,
    ) -> ToolAudit:
        clean_params = cls.sanitize(parameters)
        clean_summary = cls.sanitize(output_summary) if output_summary else None
        clean_error = cls.sanitize(error_message) if error_message else None
        uid = cls._coerce_uuid(user_id)

        audit_entry = ToolAudit(
            user_id=uid,
            agent_slug=agent_slug,
            tool_name=tool_name,
            parameters=clean_params,
            output_summary=clean_summary[:2000] if clean_summary else None,
            success=success,
            error_message=clean_error[:2000] if clean_error else None,
            duration_ms=duration_ms,
        )

        db.add(audit_entry)
        await db.commit()
        await db.refresh(audit_entry)
        return audit_entry

    @classmethod
    async def list_logs(
        cls,
        db: AsyncSession,
        user_id: Any,
        tool_name: Optional[str] = None,
        agent_slug: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ToolAudit]:
        uid = cls._coerce_uuid(user_id)
        stmt = select(ToolAudit).where(ToolAudit.user_id == uid)
        if tool_name:
            stmt = stmt.where(ToolAudit.tool_name == tool_name)

        if agent_slug:
            stmt = stmt.where(ToolAudit.agent_slug == agent_slug)
        stmt = stmt.order_by(desc(ToolAudit.created_at)).limit(limit).offset(offset)
        result = await db.execute(stmt)
        return list(result.scalars().all())
