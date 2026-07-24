"""Zentraler Modell-Katalog: die am Gateway registrierten Modelle (Spiegel von
litellm/config.yaml). Eine Quelle der Wahrheit fuer:
  - GET /v1/models (Modellwechsel-Dropdown im UI),
  - die Chat-Validierung (unbekanntes Modell -> 403 statt 502 vom Gateway).

Kommt ein Modell ins Gateway, hier ergaenzen (und in litellm/config.yaml)."""
from __future__ import annotations

# id -> Anzeigename + Herkunft. id == LiteLLM model_name (anbieter/modell).
KNOWN_MODELS: list[dict] = [
    {"id": "anthropic/claude-opus-4-8", "label": "Claude Opus 4.8", "provider": "anthropic", "local": False},
    {"id": "anthropic/claude-sonnet-5", "label": "Claude Sonnet 5", "provider": "anthropic", "local": False},
    {"id": "anthropic/claude-haiku-4-5", "label": "Claude Haiku 4.5", "provider": "anthropic", "local": False},
    {"id": "openai/gpt-4o", "label": "GPT-4o", "provider": "openai", "local": False},
    {"id": "ollama/llama3.2", "label": "Llama 3.2 (lokal)", "provider": "ollama", "local": True},
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
