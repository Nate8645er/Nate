"""OpenRouter provider (aggregates many upstream models behind one API)."""

from __future__ import annotations

from jarvis.core.config import ProviderConfig
from jarvis.llm.base import ModelInfo
from jarvis.llm.providers.openai_compat import OpenAICompatProvider


class OpenRouterProvider(OpenAICompatProvider):
    name = "openrouter"
    default_base_url = "https://openrouter.ai/api/v1"
    default_model = "anthropic/claude-sonnet-4.5"
    model_catalog = [
        ModelInfo(name="anthropic/claude-sonnet-4.5", provider="openrouter", context_window=200_000, supports_vision=True, cost_tier=2, quality=9),
        ModelInfo(name="openai/gpt-4o", provider="openrouter", context_window=128_000, supports_vision=True, cost_tier=2, quality=8),
        ModelInfo(name="google/gemini-2.5-pro", provider="openrouter", context_window=1_000_000, supports_vision=True, cost_tier=2, quality=8),
        ModelInfo(name="meta-llama/llama-3.3-70b-instruct", provider="openrouter", context_window=131_072, cost_tier=1, quality=7),
    ]

    def __init__(self, config: ProviderConfig) -> None:
        headers = {
            "HTTP-Referer": "https://github.com/Nate8645er/Nate",
            "X-Title": "JARVIS Assistant",
            **config.extra_headers,
        }
        super().__init__(config.model_copy(update={"extra_headers": headers}))

    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        raise NotImplementedError("OpenRouter does not expose an embeddings endpoint")
