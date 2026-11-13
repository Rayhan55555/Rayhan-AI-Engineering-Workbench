import time
from typing import Any, Dict, List, Literal, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.gateway.base_provider import (
    LLMResponse,
    Message,
    MessageRole,
    ModelConfig,
    ProviderHealth,
    ProviderStatus,
)
from backend.app.gateway.claude_provider import CLAUDE_MODELS, ClaudeProvider
from backend.app.gateway.cost_tracker import CostTracker
from backend.app.gateway.gemini_provider import GEMINI_MODELS, GeminiProvider
from backend.app.gateway.rate_limiter import SlidingWindowRateLimiter
from backend.app.gateway.router import GatewayTask, ModelRouter
from backend.app.models.user import User

router = APIRouter(prefix="/gateway", tags=["AI Gateway"])

# Global Gateway components
_rate_limiter = SlidingWindowRateLimiter()
_gemini = GeminiProvider()
_claude = ClaudeProvider()
_router = ModelRouter(gemini_provider=_gemini, claude_provider=_claude, rate_limiter=_rate_limiter)


class CompletionRequest(BaseModel):
    messages: List[Message]
    task_complexity: Literal["simple", "complex"] = "simple"
    agent_slug: str = Field(default="gateway", description="Calling agent identifier")
    max_tokens: int = Field(default=1000, ge=10, le=4000)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    system_prompt: Optional[str] = None
    preferred_provider: Optional[str] = None


@router.get(
    "/providers",
    response_model=List[ProviderHealth],
    summary="Get live health status and rate limit remaining per LLM provider",
)
async def get_providers_status(
    current_user: User = Depends(get_current_user),
):
    providers_health: List[ProviderHealth] = []

    # 1. Gemini
    gemini_health = await _gemini.health_check()
    gemini_health.rate_limit_remaining = _rate_limiter.remaining("gemini")
    providers_health.append(gemini_health)

    # 2. Claude
    claude_health = await _claude.health_check()
    claude_health.rate_limit_remaining = _rate_limiter.remaining("claude")
    providers_health.append(claude_health)

    return providers_health


@router.get(
    "/models",
    response_model=List[ModelConfig],
    summary="Get available models catalog, pricing per 1K tokens, and capabilities",
)
async def get_models_catalog(
    current_user: User = Depends(get_current_user),
):
    all_models = list(GEMINI_MODELS) + list(CLAUDE_MODELS)
    return all_models


@router.post(
    "/complete",
    response_model=LLMResponse,
    summary="Execute guarded LLM completion with automatic complexity routing and fallback",
)
async def complete_chat(
    body: CompletionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = GatewayTask(
        complexity=body.task_complexity,
        preferred_provider=body.preferred_provider,
        requires_reasoning=(body.task_complexity == "complex"),
    )

    try:
        response = await _router.execute_with_fallback(
            messages=body.messages,
            task=task,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
            system_prompt=body.system_prompt,
        )

        # Record usage in database
        await CostTracker.record_usage(
            db=db,
            user_id=current_user.id,
            agent_slug=body.agent_slug,
            response=response,
            task_type="completion",
        )

        return response

    except Exception as e:
        # Never expose raw keys in error output
        clean_err = str(e)
        for token in ("AIza", "sk-ant"):
            if token in clean_err:
                clean_err = "[REDACTED_API_KEY_ERROR]"

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "gateway_completion_failed",
                "message": clean_err,
                "status_code": 502,
            },
        )


@router.get(
    "/usage",
    summary="Get aggregated LLM token usage, cost in USD, and breakdown by agent/model",
)
async def get_usage_summary(
    agent_slug: Optional[str] = Query(None, description="Optional agent slug filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Regular user only sees own usage; superuser can view overall
    target_user_id = None if current_user.is_superuser else current_user.id
    summary = await CostTracker.get_usage_summary(
        db=db,
        user_id=target_user_id,
        agent_slug=agent_slug,
    )
    return summary


@router.get(
    "/usage/daily",
    summary="Get daily usage and token/cost breakdown for the last N days",
)
async def get_daily_usage(
    days: int = Query(14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target_user_id = None if current_user.is_superuser else current_user.id
    daily = await CostTracker.get_daily_usage(
        db=db,
        user_id=target_user_id,
        days=days,
    )
    return daily
