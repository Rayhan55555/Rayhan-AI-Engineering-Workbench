import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.user import User
from backend.app.mcp.audit_logger import AuditLogger


@pytest.mark.asyncio
async def test_audit_logger_creates_immutable_record(db_session: AsyncSession, test_user: User):
    """Verify audit logger writes record with latency, status, and parameters."""
    audit = await AuditLogger.log_call(
        db=db_session,
        user_id=test_user.id,
        tool_name="fs_read_file",
        parameters={"path": "src/App.tsx"},
        output_summary="Read 5432 bytes from src/App.tsx",
        success=True,
        duration_ms=45,
        agent_slug="arch-sentinel",
    )

    assert audit.id is not None
    assert audit.tool_name == "fs_read_file"
    assert audit.success is True
    assert audit.duration_ms == 45
    assert audit.agent_slug == "arch-sentinel"

    # Query back
    logs = await AuditLogger.list_logs(db_session, test_user.id, tool_name="fs_read_file")
    assert len(logs) >= 1
    assert any(str(l.id) == str(audit.id) for l in logs)


def test_audit_logger_redacts_credentials_and_api_keys():
    """Verify passwords, tokens, Gemini and Claude keys are masked before logging."""
    raw_params = {
        "password": "super_secret_db_password_123",
        "api_key": "raw_unredacted_key",
        "nested": {
            "token": "ghp_123456789012345678901234567890123456",
            "prompt": "Here is my Gemini key: AIzaSyD9837459837459384759384759384759 please analyze",
            "anthropic": "sk-ant-api03-abcdefghijklmnopqrstuvwxyz123456789",
        },
    }

    sanitized = AuditLogger.sanitize(raw_params)
    assert sanitized["password"] == "[REDACTED_CREDENTIAL]"
    assert sanitized["api_key"] == "[REDACTED_CREDENTIAL]"
    assert sanitized["nested"]["token"] == "[REDACTED_CREDENTIAL]"
    assert "AIza" not in sanitized["nested"]["prompt"]
    assert "[REDACTED_GEMINI_KEY]" in sanitized["nested"]["prompt"]
    assert "sk-ant-" not in sanitized["nested"]["anthropic"]
    assert "[REDACTED_CLAUDE_KEY]" in sanitized["nested"]["anthropic"]
