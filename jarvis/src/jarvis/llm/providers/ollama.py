"""Ollama provider for local models via Ollama's OpenAI-compatible endpoint."""

from __future__ import annotations

from jarvis.llm.base import ModelInfo
from jarvis.llm.providers.openai_compat import OpenAICompatProvider


class OllamaProvider(OpenAICompatProvider):
    name = "ollama"
    default_base_url = "http://127.0.0.1:11434/v1"
    default_model = "llama3.2"
    embedding_model = "nomic-embed-text"
    requires_api_key = False

    def _default_model_info(self, model_id: str) -> ModelInfo:
        vision = any(tag in model_id.lower() for tag in ("llava", "vision", "vl", "bakllava"))
        return ModelInfo(
            name=model_id,
            provider=self.name,
            context_window=32_768,
            supports_vision=vision,
            cost_tier=0,
            quality=5,
            local=True,
        )
