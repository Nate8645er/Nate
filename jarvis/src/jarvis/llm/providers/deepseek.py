"""DeepSeek provider."""

from __future__ import annotations

from jarvis.llm.base import ModelInfo
from jarvis.llm.providers.openai_compat import OpenAICompatProvider


class DeepSeekProvider(OpenAICompatProvider):
    name = "deepseek"
    default_base_url = "https://api.deepseek.com/v1"
    default_model = "deepseek-chat"
    model_catalog = [
        ModelInfo(name="deepseek-chat", provider="deepseek", context_window=128_000, cost_tier=1, quality=8),
        ModelInfo(name="deepseek-reasoner", provider="deepseek", context_window=128_000, cost_tier=1, quality=8, supports_tools=False),
    ]

    async def embed(self, texts: list[str], *, model: str | None = None) -> list[list[float]]:
        raise NotImplementedError("DeepSeek does not expose an embeddings endpoint")
