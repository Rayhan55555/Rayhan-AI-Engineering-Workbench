from typing import List, Literal, Optional
from pydantic import BaseModel
from backend.app.gateway.base_provider import (
    BaseProvider,
    LLMResponse,
    Message,
    ModelConfig,
    ProviderRateLimitError,
)
from backend.app.gateway.claude_provider import ClaudeProvider
from backend.app.gateway.gemini_provider import GeminiProvider
from backend.app.gateway.rate_limiter import SlidingWindowRateLimiter


class GatewayTask(BaseModel):
    complexity: Literal["simple", "complex"] = "simple"
    context_tokens_estimate: int = 500
    requires_reasoning: bool = False
    preferred_provider: Optional[str] = None


class ModelSelection(BaseModel):
    provider: str
    model: str
    reason: str
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None


class ModelRouter:
    """
    Model routing logic based on:
    - Task complexity (simple -> Flash / Haiku; complex -> Pro / Sonnet)
    - Sliding window rate limits
    - Provider health and availability
    - Automatic fallback chain
    """
    def __init__(
        self,
        gemini_provider: Optional[GeminiProvider] = None,
        claude_provider: Optional[ClaudeProvider] = None,
        rate_limiter: Optional[SlidingWindowRateLimiter] = None,
    ):
        self.gemini = gemini_provider or GeminiProvider()
        self.claude = claude_provider or ClaudeProvider()
        self.rate_limiter = rate_limiter or SlidingWindowRateLimiter()

    def route(self, task: GatewayTask) -> ModelSelection:
        """
        Determines primary model and fallback model based on complexity and rate limit state.
        """
        is_complex = (task.complexity == "complex" or task.requires_reasoning or task.context_tokens_estimate > 3000)

        # 1. Check Gemini (Primary)
        gemini_allowed = self.rate_limiter.is_allowed("gemini")
        claude_allowed = self.rate_limiter.is_allowed("claude")

        if gemini_allowed and (task.preferred_provider is None or task.preferred_provider == "gemini"):
            if is_complex:
                return ModelSelection(
                    provider="gemini",
                    model="gemini-1.5-pro",
                    reason="Complex reasoning task routed to Gemini 1.5 Pro.",
                    fallback_provider="claude",
                    fallback_model="claude-3-5-sonnet-20241022",
                )
            else:
                return ModelSelection(
                    provider="gemini",
                    model="gemini-1.5-flash",
                    reason="Routine task routed to high-speed, cost-effective Gemini 1.5 Flash.",
                    fallback_provider="claude",
                    fallback_model="claude-3-5-haiku-20241022",
                )

        # 2. Fallback to Claude if Gemini rate-limited or preferred
        if claude_allowed:
            if is_complex:
                return ModelSelection(
                    provider="claude",
                    model="claude-3-5-sonnet-20241022",
                    reason="Routed to Claude 3.5 Sonnet (Primary provider exhausted or Claude requested).",
                    fallback_provider=None,
                    fallback_model=None,
                )
            else:
                return ModelSelection(
                    provider="claude",
                    model="claude-3-5-haiku-20241022",
                    reason="Routed to Claude 3.5 Haiku as fast fallback.",
                    fallback_provider=None,
                    fallback_model=None,
                )

        # If both rate limited, force primary and let provider error trigger
        return ModelSelection(
            provider="gemini",
            model="gemini-1.5-flash",
            reason="All providers near rate limit; attempting Gemini 1.5 Flash.",
            fallback_provider="claude",
            fallback_model="claude-3-5-haiku-20241022",
        )

    async def execute_with_fallback(
        self,
        messages: List[Message],
        task: GatewayTask,
        max_tokens: int = 1000,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Executes completion via selected model. If primary fails, transparently executes fallback.
        """
        selection = self.route(task)

        # Try Primary
        primary_provider = self.gemini if selection.provider == "gemini" else self.claude
        try:
            self.rate_limiter.record_request(selection.provider)
            res = await primary_provider.complete(
                messages=messages,
                model=selection.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
            )
            return res
        except Exception as primary_error:
            # If no fallback available, re-raise
            if not selection.fallback_provider or not selection.fallback_model:
                raise primary_error

            fallback_prov = self.claude if selection.fallback_provider == "claude" else self.gemini
            self.rate_limiter.record_request(selection.fallback_provider)

            res = await fallback_prov.complete(
                messages=messages,
                model=selection.fallback_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt,
            )
            return res
