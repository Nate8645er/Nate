"""Generic local/self-hosted provider for any OpenAI-compatible endpoint.

Covers llama.cpp server, vLLM, text-generation-webui, LocalAI and similar.
Configure via ``JARVIS_LLM__PROVIDERS__LOCAL__BASE_URL``.
"""

from __future__ import annotations

from jarvis.llm.base import ModelInfo
from jarvis.llm.providers.openai_compat import OpenAICompatProvider


class LocalProvider(OpenAICompatProvider):
    name = "local"
    default_base_url = "http://127.0.0.1:8080/v1"
    default_model = "default"
    requires_api_key = False

    def _default_model_info(self, model_id: str) -> ModelInfo:
        return ModelInfo(
            name=model_id,
            provider=self.name,
            context_window=32_768,
            cost_tier=0,
            quality=5,
            local=True,
        )
