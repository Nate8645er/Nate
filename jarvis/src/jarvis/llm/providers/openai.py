"""OpenAI provider."""

from __future__ import annotations

from jarvis.llm.base import ModelInfo
from jarvis.llm.providers.openai_compat import OpenAICompatProvider


class OpenAIProvider(OpenAICompatProvider):
    name = "openai"
    default_base_url = "https://api.openai.com/v1"
    default_model = "gpt-4o"
    embedding_model = "text-embedding-3-small"
    model_catalog = [
        ModelInfo(name="gpt-4o", provider="openai", context_window=128_000, supports_vision=True, cost_tier=2, quality=8),
        ModelInfo(name="gpt-4o-mini", provider="openai", context_window=128_000, supports_vision=True, cost_tier=1, quality=6),
        ModelInfo(name="gpt-4.1", provider="openai", context_window=1_000_000, supports_vision=True, cost_tier=2, quality=8),
        ModelInfo(name="gpt-4.1-mini", provider="openai", context_window=1_000_000, supports_vision=True, cost_tier=1, quality=7),
        ModelInfo(name="o3-mini", provider="openai", context_window=200_000, cost_tier=2, quality=8),
    ]
