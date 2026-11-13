from typing import List, Optional
from backend.app.gateway.base_provider import BaseProvider, LLMResponse, Message


class FallbackChain:
    """
    Sequentially attempts an ordered list of providers until one succeeds or all fail.
    """
    def __init__(self, providers: List[BaseProvider]):
        self.providers = providers

    async def execute(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.2,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        errors = []
        for prov in self.providers:
            try:
                # Use default model for provider if not matching
                target_model = model or prov.models[0].id
                return await prov.complete(
                    messages=messages,
                    model=target_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt,
                )
            except Exception as e:
                errors.append(f"{prov.name}: {str(e)}")
                continue

        raise RuntimeError(f"All providers in fallback chain failed: {'; '.join(errors)}")
