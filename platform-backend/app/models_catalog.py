"""Zentraler Modell-Katalog: die am Gateway registrierten Modelle (Spiegel von
litellm/config.yaml). Eine Quelle der Wahrheit fuer:
  - GET /v1/models (Modellwechsel-Dropdown im UI),
  - die Chat-Validierung (unbekanntes Modell -> 403 statt 502 vom Gateway).

Kommt ein Modell ins Gateway, hier ergaenzen (und in litellm/config.yaml)."""
from __future__ import annotations

# id -> Anzeigename + Herkunft. id == LiteLLM model_name (anbieter/modell).
KNOWN_MODELS: list[dict] = [
    # --- Direkt-Anbindungen (brauchen je einen eigenen Anbieter-Key) ---
    {"id": "anthropic/claude-opus-4-8", "label": "Claude Opus 4.8", "provider": "anthropic", "local": False},
    {"id": "anthropic/claude-sonnet-5", "label": "Claude Sonnet 5", "provider": "anthropic", "local": False},
    {"id": "anthropic/claude-haiku-4-5", "label": "Claude Haiku 4.5", "provider": "anthropic", "local": False},
    {"id": "openai/gpt-4o", "label": "GPT-4o", "provider": "openai", "local": False},
    {"id": "ollama/llama3.2", "label": "Llama 3.2 (lokal)", "provider": "ollama", "local": True},

    # --- Das KI-Team ueber OpenRouter: EIN Key, 13 Anbieter ---
    # Alle IDs gegen den Live-Katalog geprueft und per ops/council_check.py
    # real getestet (13/13 haben geantwortet). Namen wie "GPT-5.6 Sol Ultra"
    # oder "Gemini 3.1 Pro Ultra" existieren NICHT und stehen hier bewusst nicht.
    {"id": "openrouter/openai/gpt-5.6-sol-pro", "label": "GPT-5.6 Sol Pro", "provider": "openai", "local": False},
    {"id": "openrouter/anthropic/claude-opus-4.8", "label": "Claude Opus 4.8 (OR)", "provider": "anthropic", "local": False},
    {"id": "openrouter/google/gemini-3.1-pro-preview", "label": "Gemini 3.1 Pro", "provider": "google", "local": False},
    {"id": "openrouter/x-ai/grok-4.5", "label": "Grok 4.5", "provider": "x-ai", "local": False},
    {"id": "openrouter/moonshotai/kimi-k3", "label": "Kimi K3", "provider": "moonshotai", "local": False},
    {"id": "openrouter/deepseek/deepseek-v4-pro", "label": "DeepSeek V4 Pro", "provider": "deepseek", "local": False},
    {"id": "openrouter/qwen/qwen3.7-max", "label": "Qwen 3.7 Max", "provider": "qwen", "local": False},
    {"id": "openrouter/meta-llama/llama-4-maverick", "label": "Llama 4 Maverick", "provider": "meta-llama", "local": False},
    {"id": "openrouter/mistralai/mistral-large-2512", "label": "Mistral Large (2512)", "provider": "mistralai", "local": False},
    {"id": "openrouter/z-ai/glm-5.2", "label": "GLM-5.2", "provider": "z-ai", "local": False},
    {"id": "openrouter/microsoft/phi-4", "label": "Phi-4", "provider": "microsoft", "local": False},
    {"id": "openrouter/cohere/command-a", "label": "Command A", "provider": "cohere", "local": False},
    {"id": "openrouter/nvidia/nemotron-3-ultra-550b-a55b", "label": "Nemotron 3 Ultra", "provider": "nvidia", "local": False},
]

_KNOWN_IDS = {m["id"] for m in KNOWN_MODELS}


def is_registered(model: str) -> bool:
    """True, wenn das Modell am Gateway registriert ist."""
    return model in _KNOWN_IDS


def models_for_plan(allowed: list) -> list[dict]:
    """Die im Tarif freigeschalteten UND am Gateway registrierten Modelle.
    '*' (Enterprise) -> alle registrierten Modelle."""
    if "*" in allowed:
        return list(KNOWN_MODELS)
    allowset = set(allowed)
    return [m for m in KNOWN_MODELS if m["id"] in allowset]
