import asyncio
import time
from typing import Any, Dict, List, Optional
from backend.app.config import settings
from backend.app.gateway.base_provider import (
    BaseProvider,
    LLMResponse,
    Message,
    MessageRole,
    ModelConfig,
    ProviderConfigError,
    ProviderHealth,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderStatus,
    ProviderTimeoutError,
)

# Claude Models Pricing:
# claude-3-5-haiku-20241022: $0.80 / 1M in ($0.0008 / 1K), $4.00 / 1M out ($0.004 / 1K)
# claude-3-5-sonnet-20241022: $3.00 / 1M in ($0.003 / 1K), $15.00 / 1M out ($0.015 / 1K)
CLAUDE_MODELS: List[ModelConfig] = [
    ModelConfig(
        id="claude-3-5-haiku-20241022",
        display_name="Claude 3.5 Haiku",
        provider="claude",
        input_cost_per_1k=0.0008,
        output_cost_per_1k=0.004,
        max_tokens=4000,
        capabilities=["fast_fallback", "code_review", "summary"],
        use_case="Fast fallback when primary provider is unavailable",
    ),
    ModelConfig(
        id="claude-3-5-sonnet-20241022",
        display_name="Claude 3.5 Sonnet",
        provider="claude",
        input_cost_per_1k=0.003,
        output_cost_per_1k=0.015,
        max_tokens=4000,
        capabilities=["deep_reasoning", "complex_architecture", "complex_fallback"],
        use_case="Complex reasoning fallback when primary provider is unavailable",
    ),
]


class ClaudeProvider(BaseProvider):
    name = "claude"
    models = CLAUDE_MODELS
    max_retries = 3
    timeout_secs = 30

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self._client = None
        self._init_sdk()

    def _init_sdk(self):
        if not self.api_key:
            return
        try:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        except Exception:
            self._client = None

    async def complete(
        self,
        messages: List[Message],
        model: str = "claude-3-5-haiku-20241022",
        max_tokens: int = 1000,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ProviderConfigError("ANTHROPIC_API_KEY is not configured.", provider=self.name)

        if not self._client:
            self._init_sdk()
            if not self._client:
                raise ProviderConfigError("Failed to initialize Anthropic client.", provider=self.name)

        model_cfg = self.get_model_config(model)
        if not model_cfg:
            model = "claude-3-5-haiku-20241022"
            model_cfg = self.get_model_config(model)

        # Separate system prompt from messages
        sys_str = system_prompt or ""
        anthropic_msgs = []
        for m in messages:
            if m.role == MessageRole.SYSTEM and not sys_str:
                sys_str = m.content
            else:
                r_str = "assistant" if m.role == MessageRole.ASSISTANT else "user"
                anthropic_msgs.append({"role": r_str, "content": m.content})

        if not anthropic_msgs:
            anthropic_msgs.append({"role": "user", "content": "Hello"})

        start_time = time.perf_counter()
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                kwargs: Dict[str, Any] = {
                    "model": model,
                    "max_tokens": min(max_tokens, model_cfg.max_tokens if model_cfg else 4000),
                    "temperature": temperature,
                    "messages": anthropic_msgs,
                }
                if sys_str:
                    kwargs["system"] = sys_str

                resp = await asyncio.wait_for(
                    self._client.messages.create(**kwargs),
                    timeout=self.timeout_secs,
                )

                latency_ms = int((time.perf_counter() - start_time) * 1000)
                text_content = ""
                if resp.content and len(resp.content) > 0:
                    text_content = resp.content[0].text

                in_tokens = getattr(resp.usage, "input_tokens", 0) or 0
                out_tokens = getattr(resp.usage, "output_tokens", 0) or 0

                cost = self.calculate_cost(model, in_tokens, out_tokens)

                return LLMResponse(
                    content=text_content,
                    model_used=model,
                    provider=self.name,
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    total_tokens=in_tokens + out_tokens,
                    cost_usd=cost,
                    latency_ms=latency_ms,
                    finish_reason="stop",
                    simulated=False,
                )

            except asyncio.TimeoutError:
                last_error = ProviderTimeoutError(
                    f"Claude API timed out after {self.timeout_secs}s on attempt {attempt}.",
                    provider=self.name,
                )
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "rate_limit" in err_str.lower():
                    raise ProviderRateLimitError(f"Claude rate limit exceeded: {err_str}", provider=self.name)
                elif "401" in err_str or "invalid x-api-key" in err_str.lower():
                    raise ProviderConfigError("Invalid Anthropic API Key.", provider=self.name)
                else:
                    last_error = ProviderResponseError(f"Claude error on attempt {attempt}: {err_str}", provider=self.name)

            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))

        if last_error:
            raise last_error
        raise ProviderResponseError("Claude call failed after retries.", provider=self.name)

    async def health_check(self) -> ProviderHealth:
        if not self.api_key:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.DOWN,
                models=[m.id for m in self.models],
                rate_limit_remaining=0,
                message="ANTHROPIC_API_KEY is not configured.",
                latency_ms=None,
            )

        start = time.perf_counter()
        try:
            res = await self.complete(
                messages=[Message(role=MessageRole.USER, content="ping")],
                model="claude-3-5-haiku-20241022",
                max_tokens=5,
            )
            lat = int((time.perf_counter() - start) * 1000)
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.HEALTHY,
                models=[m.id for m in self.models],
                rate_limit_remaining=20,
                message="Connected and operational as fallback.",
                latency_ms=lat,
            )
        except ProviderRateLimitError:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.DEGRADED,
                models=[m.id for m in self.models],
                rate_limit_remaining=0,
                message="Rate limit threshold reached.",
                latency_ms=int((time.perf_counter() - start) * 1000),
            )
        except Exception as e:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.DOWN,
                models=[m.id for m in self.models],
                rate_limit_remaining=0,
                message=f"Health check failed: {str(e)}",
                latency_ms=None,
            )
