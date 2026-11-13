from abc import ABC, abstractmethod
import enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ProviderStatus(str, enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


class MessageRole(str, enum.Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: MessageRole = MessageRole.USER
    content: str


class ModelConfig(BaseModel):
    id: str
    display_name: str
    provider: str
    input_cost_per_1k: float  # In USD
    output_cost_per_1k: float  # In USD
    max_tokens: int = 4000
    capabilities: List[str] = Field(default_factory=list)
    use_case: str


class LLMResponse(BaseModel):
    content: str
    model_used: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: int
    finish_reason: str = "stop"
    simulated: bool = False


class ProviderHealth(BaseModel):
    provider: str
    status: ProviderStatus
    models: List[str]
    rate_limit_remaining: int
    message: str
    latency_ms: Optional[int] = None


# Custom Exception Hierarchy (Never leak API keys in messages)
class GatewayError(Exception):
    """Base error for all gateway failures."""
    def __init__(self, message: str, provider: str = "gateway"):
        # Strip potential keys from error message
        clean_msg = message
        for token in ("AIza", "sk-ant", "sk-proj"):
            if token in clean_msg:
                clean_msg = clean_msg.split(token)[0] + "[REDACTED_API_KEY]"
        super().__init__(clean_msg)
        self.message = clean_msg
        self.provider = provider


class ProviderConfigError(GatewayError):
    """Raised when provider configuration or API key is missing or invalid."""
    pass


class ProviderRateLimitError(GatewayError):
    """Raised when provider quota or sliding-window rate limit is exceeded."""
    pass


class ProviderTimeoutError(GatewayError):
    """Raised when API call exceeds timeout."""
    pass


class ProviderResponseError(GatewayError):
    """Raised when provider returns an error status or malformed response."""
    pass


class BaseProvider(ABC):
    """
    Abstract Base Provider for AI Gateway.
    All LLM providers (Gemini, Claude) implement this uniform interface.
    """
    name: str
    models: List[ModelConfig]
    max_retries: int = 3
    timeout_secs: int = 30

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        model: str,
        max_tokens: int = 1000,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """Execute chat completion with retry logic and error mapping."""
        pass

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """Check provider connectivity, API key validity, and rate limit posture."""
        pass

    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        for m in self.models:
            if m.id == model_id:
                return m
        return None

    def calculate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        cfg = self.get_model_config(model_id)
        if not cfg:
            return 0.0
        cost = (input_tokens / 1000.0) * cfg.input_cost_per_1k + (output_tokens / 1000.0) * cfg.output_cost_per_1k
        return round(cost, 6)
