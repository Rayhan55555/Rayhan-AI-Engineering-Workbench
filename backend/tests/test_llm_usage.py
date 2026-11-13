import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.gateway.base_provider import LLMResponse
from backend.app.gateway.cost_tracker import CostTracker
from backend.app.models.llm_usage import LLMUsage
from backend.app.models.user import User


@pytest.mark.asyncio
async def test_cost_tracker_records_usage_and_calculates_usd(db_session: AsyncSession, test_user: User):
    """Verify CostTracker records accurate tokens and costs down to 6 decimal places."""
    fake_response = LLMResponse(
        content="Response from model",
        model_used="gemini-1.5-flash",
        provider="gemini",
        input_tokens=1000,
        output_tokens=500,
        total_tokens=1500,
        cost_usd=0.000225,  # 1K * 0.000075 + 0.5K * 0.0003
        latency_ms=280,
    )

    usage = await CostTracker.record_usage(
        db=db_session,
        user_id=test_user.id,
        agent_slug="arch-sentinel",
        response=fake_response,
        task_type="analysis",
    )

    assert usage.id is not None
    assert usage.agent_slug == "arch-sentinel"
    assert usage.cost_usd == 0.000225
    assert usage.total_tokens == 1500


@pytest.mark.asyncio
async def test_cost_tracker_summary_aggregations(db_session: AsyncSession, test_user: User):
    fake_response = LLMResponse(
        content="Aggregated response",
        model_used="gemini-1.5-flash",
        provider="gemini",
        input_tokens=800,
        output_tokens=200,
        total_tokens=1000,
        cost_usd=0.00012,
        latency_ms=150,
    )
    await CostTracker.record_usage(
        db=db_session,
        user_id=test_user.id,
        agent_slug="security-agent",
        response=fake_response,
        task_type="audit",
    )
    summary = await CostTracker.get_usage_summary(db=db_session, user_id=test_user.id)
    assert "total_requests" in summary
    assert "total_cost_usd" in summary
    assert "by_agent" in summary
    assert "by_model" in summary
    assert summary["total_requests"] >= 1

