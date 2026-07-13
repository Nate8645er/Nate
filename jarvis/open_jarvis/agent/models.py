"""Modell-Registry fuer den JARVIS-Agenten.

Hier leben alle auswaehlbaren KI-Motoren — inklusive des von dir gewuenschten
**Fable 5** (``claude-fable-5``). Die Registry ist die Datenquelle fuer den
Modell-Auswahlknopf in der CLI/UI.

Wichtig / ehrlich: Cloud-Modelle (Claude/Fable/Groq) brauchen einen API-Schluessel.
Ohne Schluessel faellt der Agent automatisch auf den lokalen, kostenlosen Planer
zurueck (``local``), damit JARVIS immer bedienbar bleibt.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentModel:
    """Ein auswaehlbarer KI-Motor fuer den Agenten."""

    key: str
    label: str
    provider: str          # "claude" | "groq" | "local"
    model_id: str          # technischer Modellname beim Anbieter ("" bei local)
    needs_key: bool
    env_key: str           # Name der Umgebungsvariable mit dem Schluessel
    description: str


# Reihenfolge = Anzeige-Reihenfolge im Auswahlknopf.
MODEL_REGISTRY: dict[str, AgentModel] = {
    "fable-5": AgentModel(
        key="fable-5",
        label="Fable 5",
        provider="claude",
        model_id="claude-fable-5",
        needs_key=True,
        env_key="ANTHROPIC_API_KEY",
        description="Claude Fable 5 — das GEHIRN von JARVIS (Standard). Denkt, plant und entscheidet.",
    ),
    "opus-4.8": AgentModel(
        key="opus-4.8",
        label="Claude Opus 4.8",
        provider="claude",
        model_id="claude-opus-4-8",
        needs_key=True,
        env_key="ANTHROPIC_API_KEY",
        description="Claude Opus 4.8 — staerkstes Reasoning fuer komplexe Aufgaben.",
    ),
    "sonnet-5": AgentModel(
        key="sonnet-5",
        label="Claude Sonnet 5",
        provider="claude",
        model_id="claude-sonnet-5",
        needs_key=True,
        env_key="ANTHROPIC_API_KEY",
        description="Claude Sonnet 5 — ausgewogen zwischen Tempo und Qualitaet.",
    ),
    "haiku-4.5": AgentModel(
        key="haiku-4.5",
        label="Claude Haiku 4.5",
        provider="claude",
        model_id="claude-haiku-4-5-20251001",
        needs_key=True,
        env_key="ANTHROPIC_API_KEY",
        description="Claude Haiku 4.5 — sehr schnell und guenstig fuer einfache Befehle.",
    ),
    "groq": AgentModel(
        key="groq",
        label="Groq (Llama)",
        provider="groq",
        model_id="llama-3.1-8b-instant",
        needs_key=True,
        env_key="GROQ_API_KEY",
        description="Groq Llama — schnelle Cloud-Alternative.",
    ),
    "local": AgentModel(
        key="local",
        label="Lokal (keyless)",
        provider="local",
        model_id="",
        needs_key=False,
        env_key="",
        description="Deterministischer lokaler Planer. Kostenlos, kein Schluessel, offline.",
    ),
}

DEFAULT_MODEL_KEY = "fable-5"
FALLBACK_MODEL_KEY = "local"
#: Das "Gehirn" von JARVIS (denkt/plant/entscheidet) — laut Systemarchitektur Fable 5,
#: NICHT Haiku.
BRAIN_MODEL_KEY = "fable-5"

# Freundliche Aliase, damit "fable", "fable5", "opus" usw. funktionieren.
_ALIASES: dict[str, str] = {
    "fable": "fable-5",
    "fable5": "fable-5",
    "fable-5": "fable-5",
    "claude-fable-5": "fable-5",
    "opus": "opus-4.8",
    "opus-4.8": "opus-4.8",
    "opus4.8": "opus-4.8",
    "claude-opus-4-8": "opus-4.8",
    "sonnet": "sonnet-5",
    "sonnet5": "sonnet-5",
    "claude-sonnet-5": "sonnet-5",
    "haiku": "haiku-4.5",
    "haiku4.5": "haiku-4.5",
    "claude-haiku-4-5-20251001": "haiku-4.5",
    "groq": "groq",
    "llama": "groq",
    "local": "local",
    "offline": "local",
    "keyless": "local",
}


def list_models() -> list[AgentModel]:
    """Alle Modelle in Anzeige-Reihenfolge (fuer den Auswahlknopf)."""

    return list(MODEL_REGISTRY.values())


def resolve_model(name: str | None) -> AgentModel:
    """Modell aus Name/Alias aufloesen. Unbekannt/leer -> Standardmodell."""

    if not name:
        return MODEL_REGISTRY[DEFAULT_MODEL_KEY]
    normalized = str(name).strip().lower()
    key = _ALIASES.get(normalized)
    if key is None and normalized in MODEL_REGISTRY:
        key = normalized
    if key is None:
        raise ValueError(
            f"Unbekanntes Modell: {name!r}. Verfuegbar: "
            + ", ".join(MODEL_REGISTRY.keys())
        )
    return MODEL_REGISTRY[key]


def default_model() -> AgentModel:
    """Das Standardmodell (Fable 5)."""

    return MODEL_REGISTRY[DEFAULT_MODEL_KEY]


def fallback_model() -> AgentModel:
    """Der keyless-Fallback (lokal)."""

    return MODEL_REGISTRY[FALLBACK_MODEL_KEY]


def brain_model() -> AgentModel:
    """Das GEHIRN von JARVIS (denkt/plant/entscheidet) — Fable 5, nicht Haiku."""

    return MODEL_REGISTRY[BRAIN_MODEL_KEY]
