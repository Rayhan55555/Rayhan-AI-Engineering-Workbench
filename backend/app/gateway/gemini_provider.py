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

# Model definitions with real pricing:
# gemini-1.5-flash: $0.075 / 1M input tokens ($0.000075 / 1K), $0.30 / 1M output tokens ($0.0003 / 1K)
# gemini-1.5-pro: $1.25 / 1M input tokens ($0.00125 / 1K), $5.00 / 1M output tokens ($0.005 / 1K)
GEMINI_MODELS: List[ModelConfig] = [
    ModelConfig(
        id="gemini-1.5-flash",
        display_name="Gemini 1.5 Flash",
        provider="gemini",
        input_cost_per_1k=0.000075,
        output_cost_per_1k=0.0003,
        max_tokens=4000,
        capabilities=["fast_reasoning", "code_review", "summary", "tool_dispatch"],
        use_case="Routine tasks, fast feedback, automated summaries",
    ),
    ModelConfig(
        id="gemini-1.5-pro",
        display_name="Gemini 1.5 Pro",
        provider="gemini",
        input_cost_per_1k=0.00125,
        output_cost_per_1k=0.005,
        max_tokens=4000,
        capabilities=["deep_reasoning", "complex_architecture", "security_analysis", "system_design"],
        use_case="Complex architectural reasoning, deep security review",
    ),
]


class GeminiProvider(BaseProvider):
    name = "gemini"
    models = GEMINI_MODELS
    max_retries = 3
    timeout_secs = 30

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._client_initialized = False
        self._init_sdk()

    def _init_sdk(self):
        if not self.api_key:
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client_initialized = True
        except Exception:
            self._client_initialized = False

    async def complete(
        self,
        messages: List[Message],
        model: str = "gemini-1.5-flash",
        max_tokens: int = 1000,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise ProviderConfigError("GEMINI_API_KEY is not configured.", provider=self.name)

        if not self._client_initialized:
            self._init_sdk()
            if not self._client_initialized:
                raise ProviderConfigError("Failed to initialize Google Generative AI client.", provider=self.name)

        model_cfg = self.get_model_config(model)
        if not model_cfg:
            model = "gemini-1.5-flash"
            model_cfg = self.get_model_config(model)

        import google.generativeai as genai

        # Construct generation prompt and history
        system_instruction = system_prompt
        for m in messages:
            if m.role == MessageRole.SYSTEM and not system_instruction:
                system_instruction = m.content

        # Combine user/assistant turns
        contents = []
        for m in messages:
            if m.role != MessageRole.SYSTEM:
                role_str = "model" if m.role == MessageRole.ASSISTANT else "user"
                contents.append({"role": role_str, "parts": [m.content]})

        if not contents:
            contents.append({"role": "user", "parts": ["Hello"]})

        gen_config = genai.types.GenerationConfig(
            max_output_tokens=min(max_tokens, model_cfg.max_tokens if model_cfg else 4000),
            temperature=temperature,
        )

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        start_time = time.perf_counter()
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                loop = asyncio.get_running_loop()
                model_instance = genai.GenerativeModel(
                    model_name=model,
                    system_instruction=system_instruction,
                    safety_settings=safety_settings,
                    generation_config=gen_config,
                )

                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: model_instance.generate_content(contents),
                    ),
                    timeout=self.timeout_secs,
                )

                latency_ms = int((time.perf_counter() - start_time) * 1000)
                text_content = response.text if response and hasattr(response, "text") else ""

                # Token usage estimation or extraction
                in_tokens = 0
                out_tokens = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    in_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                    out_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

                if in_tokens == 0:
                    # Estimate ~4 chars per token
                    in_tokens = max(1, sum(len(m.content) for m in messages) // 4)
                if out_tokens == 0:
                    out_tokens = max(1, len(text_content) // 4)

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
                    f"Gemini API timed out after {self.timeout_secs}s on attempt {attempt}.",
                    provider=self.name,
                )
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower() or "resource_exhausted" in err_str.lower():
                    raise ProviderRateLimitError(f"Gemini rate limit exceeded: {err_str}", provider=self.name)
                elif "API_KEY_INVALID" in err_str or "invalid api key" in err_str.lower():
                    raise ProviderConfigError("Invalid Gemini API Key.", provider=self.name)
                else:
                    last_error = ProviderResponseError(f"Gemini error on attempt {attempt}: {err_str}", provider=self.name)

            # Exponential backoff retry
            if attempt < self.max_retries:
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))

        if last_error:
            raise last_error
        raise ProviderResponseError("Gemini call failed after retries.", provider=self.name)

    async def health_check(self) -> ProviderHealth:
        if not self.api_key:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.DOWN,
                models=[m.id for m in self.models],
                rate_limit_remaining=0,
                message="GEMINI_API_KEY is not configured.",
                latency_ms=None,
            )

        start = time.perf_counter()
        try:
            # Ping model with minimal prompt
            res = await self.complete(
                messages=[Message(role=MessageRole.USER, content="ping")],
                model="gemini-1.5-flash",
                max_tokens=5,
            )
            lat = int((time.perf_counter() - start) * 1000)
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.HEALTHY,
                models=[m.id for m in self.models],
                rate_limit_remaining=15,  # Free/Tier default per minute
                message="Connected and operational.",
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
