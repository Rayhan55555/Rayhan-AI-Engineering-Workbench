import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.gateway.base_provider import (
    LLMResponse,
    Message,
    MessageRole,
    ModelConfig,
    ProviderConfigError,
    ProviderHealth,
    ProviderRateLimitError,
    ProviderStatus,
    ProviderTimeoutError,
)
from backend.app.gateway.claude_provider import ClaudeProvider
from backend.app.gateway.gemini_provider import GeminiProvider
from backend.app.gateway.rate_limiter import SlidingWindowRateLimiter
from backend.app.gateway.router import GatewayTask, ModelRouter


# ==============================================================================
# [MOCK] Provider Health & Model Routing Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_provider_health_check_unconfigured_status():
    """[MOCK] When API key is empty, provider health check returns DOWN without crash."""
    gemini = GeminiProvider(api_key="")
    health = await gemini.health_check()
    assert health.status == ProviderStatus.DOWN
    assert "not configured" in health.message.lower()

    claude = ClaudeProvider(api_key="")
    claude_health = await claude.health_check()
    assert claude_health.status == ProviderStatus.DOWN


def test_model_router_simple_task():
    """[MOCK] Simple task routes to gemini-1.5-flash with claude haiku fallback."""
    router = ModelRouter()
    task = GatewayTask(complexity="simple", requires_reasoning=False)
    selection = router.route(task)

    assert selection.provider == "gemini"
    assert selection.model == "gemini-1.5-flash"
    assert selection.fallback_provider == "claude"
    assert "haiku" in selection.fallback_model


def test_model_router_complex_task():
    """[MOCK] Complex task routes to gemini-1.5-pro with claude sonnet fallback."""
    router = ModelRouter()
    task = GatewayTask(complexity="complex", requires_reasoning=True)
    selection = router.route(task)

    assert selection.provider == "gemini"
    assert selection.model == "gemini-1.5-pro"
    assert selection.fallback_provider == "claude"
    assert "sonnet" in selection.fallback_model


def test_rate_limiter_sliding_window_enforcement():
    """[MOCK] Rate limiter restricts requests once window threshold is reached."""
    limiter = SlidingWindowRateLimiter(max_requests_per_window=3, window_seconds=60)
    assert limiter.is_allowed("gemini")
    limiter.record_request("gemini")
    limiter.record_request("gemini")
    limiter.record_request("gemini")

    assert not limiter.is_allowed("gemini")
    assert limiter.remaining("gemini") == 0


@pytest.mark.asyncio
async def test_fallback_chain_trigger_on_primary_failure():
    """[MOCK] Router transparently executes fallback when primary provider raises an error."""
    mock_gemini = GeminiProvider(api_key="mock-key")
    mock_gemini.complete = AsyncMock(side_effect=ProviderRateLimitError("Quota exceeded", provider="gemini"))

    mock_claude = ClaudeProvider(api_key="mock-key")
    mock_claude.complete = AsyncMock(
        return_value=LLMResponse(
            content="Fallback answer from Claude",
            model_used="claude-3-5-haiku-20241022",
            provider="claude",
            input_tokens=15,
            output_tokens=25,
            total_tokens=40,
            cost_usd=0.0001,
            latency_ms=250,
        )
    )

    router = ModelRouter(gemini_provider=mock_gemini, claude_provider=mock_claude)
    task = GatewayTask(complexity="simple")

    res = await router.execute_with_fallback(
        messages=[Message(role=MessageRole.USER, content="Hello")],
        task=task,
    )

    assert res.provider == "claude"
    assert "Fallback answer from Claude" in res.content
    assert mock_gemini.complete.called
    assert mock_claude.complete.called


def test_api_key_never_exposed_in_exception():
    """[MOCK] API keys must never be leaked inside GatewayError exception messages."""
    fake_secret = "AIzaSyFakeKey1234567890SecretValue"
    err = ProviderConfigError(f"Connection failed for key {fake_secret}")
    assert fake_secret not in str(err)
    assert "[REDACTED_API_KEY]" in str(err)
