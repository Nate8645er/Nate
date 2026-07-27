"""Nutzungsbasierte Meldung an Stripe (Billing-Meters-API) -- optional, per
STRIPE_SECRET_KEY. Ohne den Key: no-op, kein Fehler, Verbrauch bleibt nur
lokal in usage_events/GET /v1/usage sichtbar.

Bewusst per rohem HTTP (httpx) statt stripe-python-SDK -- konsistent mit
app/billing.py, das eingehende Webhooks ebenfalls ohne SDK verifiziert
(Master-Prompt: keine unnoetige Abhaengigkeit fuer etwas, das eine einzelne
HTTP-Anfrage ist).

EHRLICHER STAND: In dieser Umgebung existiert kein echter Stripe-Account/
Secret-Key, daher konnte der tatsaechliche API-Aufruf nicht gegen die echte
Stripe-API verifiziert werden -- nur die Aufrufstruktur (Endpoint, Feldnamen,
Auth-Schema) ist gegen die oeffentliche Stripe-Dokumentation gebaut und mit
einem gefaelschten HTTP-Client getestet (tests/test_stripe_usage.py). Ein
Fehlschlag hier darf NIE einen Chat-Request scheitern lassen -- Best-Effort,
mit Logging statt Exception nach aussen."""
from __future__ import annotations

import logging

import httpx

from .config import settings

log = logging.getLogger("platform.stripe_usage")

STRIPE_API_BASE = "https://api.stripe.com/v1"

# Muss in Stripe als Billing-Meter mit exakt diesem event_name angelegt sein
# (Stripe Dashboard -> Billing -> Meters), sonst schlaegt jede Meldung fehl.
METER_EVENT_NAME = "platform_tokens"


async def report_usage(stripe_customer_id: str | None, tokens_total: int) -> None:
    """Meldet `tokens_total` als Meter-Event fuer `stripe_customer_id`.
    No-op ohne STRIPE_SECRET_KEY, ohne verknuepften Kunden, oder bei
    tokens_total <= 0. Wirft NIE -- Fehler werden geloggt, nicht
    durchgereicht, damit ein Stripe-Ausfall nie einen Chat-Request scheitern
    laesst."""
    if not settings.stripe_secret_key:
        return
    if not stripe_customer_id or tokens_total <= 0:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{STRIPE_API_BASE}/billing/meter_events",
                auth=(settings.stripe_secret_key, ""),
                data={
                    "event_name": METER_EVENT_NAME,
                    "payload[stripe_customer_id]": stripe_customer_id,
                    "payload[value]": str(tokens_total),
                },
            )
        if resp.status_code >= 400:
            log.warning(
                "Stripe Meter-Event fehlgeschlagen (%s) fuer Kunde %s: %s",
                resp.status_code, stripe_customer_id, resp.text[:300],
            )
    except httpx.HTTPError as exc:
        log.warning("Stripe Meter-Event nicht erreichbar fuer Kunde %s: %s", stripe_customer_id, exc)
