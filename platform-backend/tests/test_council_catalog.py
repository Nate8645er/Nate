"""Tests des KI-Team-Katalogs: die 13 Council-Modelle muessen im
Modell-Katalog, im LiteLLM-Gateway UND in den Tarifen konsistent sein.

Faengt genau den Fehler ab, der sonst erst zur Laufzeit auffaellt: ein Modell
ist im Tarif freigeschaltet, aber am Gateway gar nicht registriert (-> 502)
oder umgekehrt.
"""
from __future__ import annotations

import json
import pathlib
import re

from app.models_catalog import KNOWN_MODELS, is_registered

ROOT = pathlib.Path(__file__).resolve().parent.parent
LITELLM_CFG = (ROOT / "litellm" / "config.yaml").read_text(encoding="utf-8")
PLAN_MIG = (ROOT / "migrations" / "008_openrouter_plans.sql").read_text(encoding="utf-8")

# Die 13 Anbieter des Teams, je ein Modell — verifiziert via ops/council_check.py.
COUNCIL_IDS = [
    "openrouter/openai/gpt-5.6-sol-pro",
    "openrouter/anthropic/claude-opus-4.8",
    "openrouter/google/gemini-3.1-pro-preview",
    "openrouter/x-ai/grok-4.5",
    "openrouter/moonshotai/kimi-k3",
    "openrouter/deepseek/deepseek-v4-pro",
    "openrouter/qwen/qwen3.7-max",
    "openrouter/meta-llama/llama-4-maverick",
    "openrouter/mistralai/mistral-large-2512",
    "openrouter/z-ai/glm-5.2",
    "openrouter/microsoft/phi-4",
    "openrouter/cohere/command-a",
    "openrouter/nvidia/nemotron-3-ultra-550b-a55b",
]

# Namen, die kursieren, aber NICHT existieren — duerfen nie im Katalog landen.
NONEXISTENT = [
    "gpt-5.6-sol-ultra",
    "gemini-3.1-pro-ultra",
    "grok-4.5-heavy",
    "qwen-3.8-max",
    "mistral-large-3",
    "command-a-plus",
    "nemotron-ultra",
]


def test_council_has_thirteen_distinct_providers():
    providers = {mid.split("/")[1] for mid in COUNCIL_IDS}
    assert len(COUNCIL_IDS) == 13
    assert len(providers) == 13, f"Anbieter nicht eindeutig: {providers}"


def test_all_council_models_are_in_catalog():
    for mid in COUNCIL_IDS:
        assert is_registered(mid), f"{mid} fehlt in models_catalog.KNOWN_MODELS"


def test_all_council_models_are_registered_at_gateway():
    for mid in COUNCIL_IDS:
        assert f"model_name: {mid}" in LITELLM_CFG, f"{mid} fehlt in litellm/config.yaml"


def test_no_nonexistent_model_names_anywhere():
    catalog_ids = " ".join(m["id"] for m in KNOWN_MODELS)
    for fake in NONEXISTENT:
        assert fake not in catalog_ids, f"Erfundener Modellname im Katalog: {fake}"
        assert fake not in LITELLM_CFG, f"Erfundener Modellname im Gateway: {fake}"
        assert fake not in PLAN_MIG, f"Erfundener Modellname in den Tarifen: {fake}"


def test_plan_models_are_all_registered():
    """Jedes in Migration 008 freigeschaltete Modell muss am Gateway
    registriert sein — sonst gaebe es 403/502 statt einer nutzbaren Auswahl."""
    for raw in re.findall(r'"([a-z0-9\-]+/[^"]+)"', PLAN_MIG):
        assert is_registered(raw), f"Tarif schaltet unbekanntes Modell frei: {raw}"


def test_business_plan_contains_full_council():
    block = PLAN_MIG.split("WHERE code = 'business'")[0]
    for mid in COUNCIL_IDS:
        assert f'"{mid}"' in block, f"Business-Tarif fehlt Team-Mitglied: {mid}"


def test_openrouter_models_use_single_key():
    """Alle Team-Modelle laufen ueber EINEN OpenRouter-Key (kein Anbieter-Key je Firma)."""
    for mid in COUNCIL_IDS:
        idx = LITELLM_CFG.index(f"model_name: {mid}")
        block = LITELLM_CFG[idx: idx + 400]
        assert "os.environ/OPENROUTER_API_KEY" in block, f"{mid} nutzt nicht den OpenRouter-Key"


def test_catalog_entries_wellformed():
    for m in KNOWN_MODELS:
        assert set(m) == {"id", "label", "provider", "local", "vision"}
        assert m["id"] and m["label"] and m["provider"]
        assert isinstance(m["local"], bool)
        assert isinstance(m["vision"], bool)
