"""Mistral AI provider (their API is OpenAI-compatible for chat and embeddings)."""

from __future__ import annotations

from jarvis.llm.base import ModelInfo
from jarvis.llm.providers.openai_compat import OpenAICompatProvider


class MistralProvider(OpenAICompatProvider):
    name = "mistral"
    default_base_url = "https://api.mistral.ai/v1"
    default_model = "mistral-large-latest"
    embedding_model = "mistral-embed"
    model_catalog = [
        ModelInfo(name="mistral-large-latest", provider="mistral", context_window=131_072, cost_tier=2, quality=8),
        ModelInfo(name="mistral-small-latest", provider="mistral", context_window=131_072, cost_tier=1, quality=6),
        ModelInfo(name="pixtral-large-latest", provider="mistral", context_window=131_072, supports_vision=True, cost_tier=2, quality=7),
        ModelInfo(name="codestral-latest", provider="mistral", context_window=262_144, cost_tier=1, quality=7),
    ]
