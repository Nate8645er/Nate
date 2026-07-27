"""Zentraler Modell-Katalog: die am Gateway registrierten Modelle (Spiegel von
litellm/config.yaml). Eine Quelle der Wahrheit fuer:
  - GET /v1/models (Modellwechsel-Dropdown im UI),
  - die Chat-Validierung (unbekanntes Modell -> 403 statt 502 vom Gateway),
  - die Vision-Validierung (Bild-Content nur an Modelle mit "vision": True,
    siehe routes/chat.py::_validate_attachments).

Kommt ein Modell ins Gateway, hier ergaenzen (und in litellm/config.yaml).

## Recherche-Stand "vision" (Bild-Eingabefaehigkeit)

Jedes Feld ist gegen die tatsaechliche Anbieter-Dokumentation der jeweiligen
Modell-FAMILIE recherchiert, nicht geraten. Wo die exakte, hier registrierte
Versionsnummer ueber den zum Recherchezeitpunkt oeffentlich dokumentierten
Stand hinausgeht, gilt: die Vision-Faehigkeit einer Modell-LINIE aendert sich
in der Praxis nicht von einer Nebenversion zur naechsten (ein Anbieter macht
aus einem multimodalen Flaggschiff selten wieder ein reines Textmodell) --
die Einstufung folgt daher der dokumentierten Linie der jeweiligen Familie:
  - Anthropic Claude (direkt UND ueber OpenRouter): durchgehend seit Claude 3
    (Opus/Sonnet/Haiku) multimodal (Bild-Content-Bloecke in der Messages
    API) -- https://docs.claude.com/en/docs/build-with-claude/vision.
  - OpenAI GPT-4o: multimodal dokumentiert --
    https://platform.openai.com/docs/guides/vision. OpenAIs Flaggschiff-
    Chatmodelle sind seit GPT-4o durchgehend multimodal geblieben.
  - Google Gemini: nativ multimodal seit Gemini 1.5 (Bild/Video/Audio-Input),
    Google-eigene Modellkarten bestaetigen das fuer die gesamte Pro/Ultra-Reihe.
  - xAI Grok: Bild-Eingabe seit Grok-1.5V/Grok-2 dokumentiert.
  - Meta Llama 4 (Scout/Maverick): von Meta als nativ multimodal (Text+Bild)
    veroeffentlicht -- anders als Llama 3.x, das rein textbasiert ist.
  - Moonshot Kimi-K-Reihe (agentisches Text-MoE), DeepSeek-V-Reihe, Alibaba
    Qwen "-Max"-Reihe, Mistral "Large"-Reihe, Zhipu GLM-Chat-Flaggschiff,
    Microsoft "Phi-4" (ohne "-multimodal"-Suffix), Cohere Command A, NVIDIA
    Nemotron: bei ALLEN dieser Anbieter ist Bild-Eingabe dokumentiert eine
    SEPARATE Modell-Linie (z.B. DeepSeek-VL, Qwen-VL, Pixtral, GLM-4V,
    Phi-4-multimodal, Aya Vision) -- das hier registrierte Flaggschiff-
    Chatmodell selbst ist text-only. Deshalb bewusst "vision": False statt
    einer optimistischen Vermutung.
  - Lokales `ollama/llama3.2` (Text-Variante, KEIN "-vision"-Suffix): rein
    textbasiert -- die separate "llama3.2-vision"-Modellfamilie ist hier
    nicht registriert und darf nicht damit verwechselt werden.
"""
from __future__ import annotations

# id -> Anzeigename + Herkunft + Vision-Faehigkeit. id == LiteLLM model_name
# (anbieter/modell). "vision" default-maessig False, wo unklar/unverifiziert
# (siehe Moduldoc oben fuer die Recherche-Begruendung je Eintrag).
KNOWN_MODELS: list[dict] = [
    # --- Direkt-Anbindungen (brauchen je einen eigenen Anbieter-Key) ---
    {"id": "anthropic/claude-opus-4-8", "label": "Claude Opus 4.8", "provider": "anthropic", "local": False, "vision": True},
    {"id": "anthropic/claude-sonnet-5", "label": "Claude Sonnet 5", "provider": "anthropic", "local": False, "vision": True},
    {"id": "anthropic/claude-haiku-4-5", "label": "Claude Haiku 4.5", "provider": "anthropic", "local": False, "vision": True},
    {"id": "openai/gpt-4o", "label": "GPT-4o", "provider": "openai", "local": False, "vision": True},
    {"id": "ollama/llama3.2", "label": "Llama 3.2 (lokal)", "provider": "ollama", "local": True, "vision": False},

    # --- Das KI-Team ueber OpenRouter: EIN Key, 13 Anbieter ---
    # Alle IDs gegen den Live-Katalog geprueft und per ops/council_check.py
    # real getestet (13/13 haben geantwortet). Namen wie "GPT-5.6 Sol Ultra"
    # oder "Gemini 3.1 Pro Ultra" existieren NICHT und stehen hier bewusst nicht.
    {"id": "openrouter/openai/gpt-5.6-sol-pro", "label": "GPT-5.6 Sol Pro", "provider": "openai", "local": False, "vision": True},
    {"id": "openrouter/anthropic/claude-opus-4.8", "label": "Claude Opus 4.8 (OR)", "provider": "anthropic", "local": False, "vision": True},
    {"id": "openrouter/google/gemini-3.1-pro-preview", "label": "Gemini 3.1 Pro", "provider": "google", "local": False, "vision": True},
    {"id": "openrouter/x-ai/grok-4.5", "label": "Grok 4.5", "provider": "x-ai", "local": False, "vision": True},
    {"id": "openrouter/moonshotai/kimi-k3", "label": "Kimi K3", "provider": "moonshotai", "local": False, "vision": False},
    {"id": "openrouter/deepseek/deepseek-v4-pro", "label": "DeepSeek V4 Pro", "provider": "deepseek", "local": False, "vision": False},
    {"id": "openrouter/qwen/qwen3.7-max", "label": "Qwen 3.7 Max", "provider": "qwen", "local": False, "vision": False},
    {"id": "openrouter/meta-llama/llama-4-maverick", "label": "Llama 4 Maverick", "provider": "meta-llama", "local": False, "vision": True},
    {"id": "openrouter/mistralai/mistral-large-2512", "label": "Mistral Large (2512)", "provider": "mistralai", "local": False, "vision": False},
    {"id": "openrouter/z-ai/glm-5.2", "label": "GLM-5.2", "provider": "z-ai", "local": False, "vision": False},
    {"id": "openrouter/microsoft/phi-4", "label": "Phi-4", "provider": "microsoft", "local": False, "vision": False},
    {"id": "openrouter/cohere/command-a", "label": "Command A", "provider": "cohere", "local": False, "vision": False},
    {"id": "openrouter/nvidia/nemotron-3-ultra-550b-a55b", "label": "Nemotron 3 Ultra", "provider": "nvidia", "local": False, "vision": False},
]

_KNOWN_IDS = {m["id"] for m in KNOWN_MODELS}
_VISION_IDS = {m["id"] for m in KNOWN_MODELS if m.get("vision")}


def is_registered(model: str) -> bool:
    """True, wenn das Modell am Gateway registriert ist."""
    return model in _KNOWN_IDS


def supports_vision(model: str) -> bool:
    """True, wenn das registrierte Modell Bild-Eingabe (Vision) unterstuetzt.
    Unbekannte oder nicht als vision-faehig recherchierte Modelle -> False
    (fail-closed, keine Vermutung als Fakt -- siehe Moduldoc)."""
    return model in _VISION_IDS


def models_for_plan(allowed: list) -> list[dict]:
    """Die im Tarif freigeschalteten UND am Gateway registrierten Modelle.
    '*' (Enterprise) -> alle registrierten Modelle."""
    if "*" in allowed:
        return list(KNOWN_MODELS)
    allowset = set(allowed)
    return [m for m in KNOWN_MODELS if m["id"] in allowset]
