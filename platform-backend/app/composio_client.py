"""Duenne Anbindung an Composio (composio-core) -- ersetzt den TODO-
Platzhalter in app/routes/integrations.py mit einem echten OAuth-Anstoss,
sobald COMPOSIO_API_KEY gesetzt ist.

Ohne den Key bleibt alles wie zuvor: build_toolset() liefert None, die Route
faellt auf das reine Geruest zurueck (status bleibt 'disconnected'). Es gibt
in dieser Umgebung keinen echten Composio-Account -- das hier ist der
Code-Pfad fuer den Tag, an dem einer existiert, nicht eine vorgetaeuschte
Verbindung."""
from __future__ import annotations

from .config import settings

# Composio meldet den Verbindungsstatus mit eigenen Werten (z.B. "ACTIVE",
# "INITIATED", "FAILED"). Unsere Tabelle kennt nur 'connected'/'disconnected'
# (Migration 007) -- alles ausser einem aktiven Zustand zaehlt als
# 'disconnected', damit kein neuer Statuswert in der DB noetig ist.
_ACTIVE_STATUSES = {"ACTIVE"}


def build_toolset():
    """None ohne COMPOSIO_API_KEY (Feature bleibt aus, Verhalten unveraendert
    zum bisherigen Geruest). Lazy-Import von composio, damit die
    Abhaengigkeit nur geladen wird, wenn sie wirklich gebraucht wird."""
    if not settings.composio_api_key:
        return None
    from composio import ComposioToolSet  # noqa: PLC0415

    return ComposioToolSet(api_key=settings.composio_api_key)


def map_status(composio_status: str) -> str:
    return "connected" if composio_status in _ACTIVE_STATUSES else "disconnected"
