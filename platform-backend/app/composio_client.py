"""Duenne Anbindung an Composio (composio-core) -- ersetzt den TODO-
Platzhalter in app/routes/integrations.py mit einem echten OAuth-Anstoss,
sobald COMPOSIO_API_KEY gesetzt ist.

Ohne den Key bleibt alles wie zuvor: build_toolset() liefert None, die Route
faellt auf das reine Geruest zurueck (status bleibt 'disconnected'). Es gibt
in dieser Umgebung keinen echten Composio-Account -- das hier ist der
Code-Pfad fuer den Tag, an dem einer existiert, nicht eine vorgetaeuschte
Verbindung."""
from __future__ import annotations

import logging
import os

from .config import settings

log = logging.getLogger("platform.composio_client")

# Composio meldet den Verbindungsstatus mit eigenen Werten (z.B. "ACTIVE",
# "INITIATED", "FAILED"). Unsere Tabelle kennt nur 'connected'/'disconnected'
# (Migration 007) -- alles ausser einem aktiven Zustand zaehlt als
# 'disconnected', damit kein neuer Statuswert in der DB noetig ist.
_ACTIVE_STATUSES = {"ACTIVE"}

# Unser Provider-Code "google" (Migration 007, integrations.py) ist bewusst
# knapp, aber Composio kennt kein einzelnes "google"-App -- Google ist bei
# Composio in einzelne Produkte aufgeteilt (Gmail, Google Sheets, Google
# Calendar, ...). "gmail" ist Composios oeffentlich dokumentierter Standard-
# Slug fuer Gmail -- HIER ABER UNGEPRUEFT: es existiert kein echter Composio-
# Account in dieser Umgebung, um das live zu bestaetigen. Deshalb per
# Umgebungsvariable ueberschreibbar, statt den Rateversuch stillschweigend
# als Tatsache zu behandeln -- vor dem ersten echten Einsatz im Composio-
# Dashboard nachschlagen und COMPOSIO_GOOGLE_APP_SLUG setzen, falls der
# tatsaechliche Slug abweicht.
_DEFAULT_GOOGLE_APP_SLUG = "gmail"


def composio_app_slug(provider: str) -> str:
    if provider == "google":
        slug = os.environ.get("COMPOSIO_GOOGLE_APP_SLUG", "").strip() or _DEFAULT_GOOGLE_APP_SLUG
        if slug == _DEFAULT_GOOGLE_APP_SLUG:
            log.info(
                "Provider 'google' -> Composio-App '%s' (unverifizierter Standardwert, "
                "siehe COMPOSIO_GOOGLE_APP_SLUG in composio_client.py)", slug,
            )
        return slug
    return provider


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
