"""Abrechnung (Phase 4): Stripe-Signaturpruefung, Tarif-Zuordnung,
Idempotenz und Anwendung von Abo-Aenderungen.

Bewusst ohne Stripe-SDK: die Signaturpruefung ist HMAC-SHA256 aus der
Standardbibliothek (Master-Prompt: Stdlib vor neuer Dependency).
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time

from .db import admin_tx, tenant_tx

log = logging.getLogger("platform.billing")

# Stripe-Standardtoleranz gegen Replay alter Events.
SIGNATURE_TOLERANCE_S = 300

# Abo-Zustaende, die den Zugang offen halten. Alles andere sperrt den Mandanten
# (auth.py lehnt nicht-aktive Mandanten mit 403 ab).
ACTIVE_STATUSES = {"active", "trialing"}


# --------------------------------------------------------------------------
# Signatur
# --------------------------------------------------------------------------
def parse_stripe_signature(header: str) -> tuple[int | None, list[str]]:
    """Zerlegt 'Stripe-Signature: t=...,v1=...,v1=...' in (timestamp, [v1...])."""
    ts: int | None = None
    sigs: list[str] = []
    for part in (header or "").split(","):
        key, _, value = part.strip().partition("=")
        if key == "t":
            try:
                ts = int(value)
            except ValueError:
                ts = None
        elif key == "v1":
            sigs.append(value)
    return ts, sigs


def verify_stripe_signature(
    raw_body: bytes,
    header: str,
    secret: str,
    now: float | None = None,
    tolerance: int = SIGNATURE_TOLERANCE_S,
) -> bool:
    """Prueft die Stripe-Signatur konstant-Zeit inkl. Zeitfenster (Replay-Schutz)."""
    if not secret:
        return False
    ts, sigs = parse_stripe_signature(header)
    if ts is None or not sigs:
        return False
    current = time.time() if now is None else now
    if abs(current - ts) > tolerance:
        return False
    signed_payload = f"{ts}.".encode() + raw_body
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, s) for s in sigs)


# --------------------------------------------------------------------------
# Tarif-Zuordnung
# --------------------------------------------------------------------------
def _price_map_from_env() -> dict[str, str]:
    """STRIPE_PRICE_MAP='price_123:pro,price_456:business' -> {price_id: plan_code}."""
    raw = os.environ.get("STRIPE_PRICE_MAP", "")
    out: dict[str, str] = {}
    for pair in raw.split(","):
        pid, _, code = pair.strip().partition(":")
        if pid and code:
            out[pid] = code
    return out


def plan_code_from_event(obj: dict) -> str | None:
    """Ermittelt den Tarif aus einem Stripe-Objekt. Reihenfolge:
    1. metadata.plan_code (empfohlen: bei Checkout/Subscription setzen)
    2. Preis-Kennung aus items -> STRIPE_PRICE_MAP
    """
    meta = obj.get("metadata") or {}
    if meta.get("plan_code"):
        return str(meta["plan_code"]).strip().lower()

    price_map = _price_map_from_env()
    items = ((obj.get("items") or {}).get("data")) or []
    for item in items:
        price_id = ((item.get("price") or {}).get("id")) or ""
        if price_id in price_map:
            return price_map[price_id]
    # Checkout-Session ohne expandierte Items: einzelne price-Kennung.
    single = obj.get("price") or {}
    if single.get("id") in price_map:
        return price_map[single["id"]]
    return None


# --------------------------------------------------------------------------
# Idempotenz
# --------------------------------------------------------------------------
def claim_event(conn, provider: str, event_id: str) -> bool:
    """Atomare Variante: belegt das Event INNERHALB der uebergebenen Transaktion.

    Damit sind Belegung und die eigentliche Verarbeitung (z. B. Mandant anlegen)
    ein einziger Commit: bricht die Verarbeitung ab, wird auch die Belegung
    zurueckgerollt und eine Wiederzustellung greift korrekt.
    True = neu, False = bereits verarbeitet.
    """
    if not event_id:
        return True  # ohne Kennung keine Idempotenz moeglich; nicht blockieren
    row = conn.execute(
        "INSERT INTO processed_webhooks (provider, event_id) VALUES (%s, %s) "
        "ON CONFLICT (provider, event_id) DO NOTHING RETURNING event_id",
        (provider, event_id),
    ).fetchone()
    return row is not None


def mark_processed(provider: str, event_id: str) -> bool:
    """Bequeme Variante mit eigener Transaktion — nur fuer Ereignisse, deren
    Verarbeitung ohnehin wiederholbar ist (Zustandsupdates wie 'status=active').
    Fuer alles, was etwas ANLEGT, claim_event in der Arbeits-Transaktion nutzen."""
    if not event_id:
        return True
    with admin_tx() as conn:
        return claim_event(conn, provider, event_id)


# --------------------------------------------------------------------------
# Anwendung von Abo-Aenderungen
# --------------------------------------------------------------------------
def find_tenant_by_customer(customer_id: str) -> str | None:
    if not customer_id:
        return None
    with admin_tx() as conn:
        row = conn.execute(
            "SELECT id FROM tenants WHERE stripe_customer_id = %s", (customer_id,)
        ).fetchone()
    return str(row["id"]) if row else None


def link_stripe_customer(tenant_id: str, customer_id: str, subscription_id: str | None) -> None:
    with admin_tx() as conn:
        conn.execute(
            "UPDATE tenants SET stripe_customer_id = %s, stripe_subscription_id = %s "
            "WHERE id = %s",
            (customer_id or None, subscription_id or None, tenant_id),
        )


def apply_subscription_state(
    tenant_id: str,
    plan_code: str | None,
    subscription_status: str,
    current_period_end=None,
    subscription_id: str | None = None,
) -> None:
    """Setzt Tarif + Abo-Zustand am Mandanten. Ein nicht-aktives Abo sperrt den
    Mandanten (auth.py -> 403), ein wieder aktives entsperrt ihn."""
    tenant_status = "active" if subscription_status in ACTIVE_STATUSES else "suspended"
    with admin_tx() as conn:
        plan_id = None
        if plan_code:
            plan = conn.execute(
                "SELECT id FROM plans WHERE code = %s", (plan_code,)
            ).fetchone()
            if plan is None:
                log.warning("Unbekannter Tarif '%s' im Abo-Event", plan_code)
            else:
                plan_id = plan["id"]

        if plan_id is not None:
            conn.execute(
                "UPDATE tenants SET plan_id = %s, subscription_status = %s, status = %s, "
                "current_period_end = %s, stripe_subscription_id = COALESCE(%s, stripe_subscription_id) "
                "WHERE id = %s",
                (plan_id, subscription_status, tenant_status, current_period_end,
                 subscription_id, tenant_id),
            )
        else:
            conn.execute(
                "UPDATE tenants SET subscription_status = %s, status = %s, "
                "current_period_end = %s, stripe_subscription_id = COALESCE(%s, stripe_subscription_id) "
                "WHERE id = %s",
                (subscription_status, tenant_status, current_period_end,
                 subscription_id, tenant_id),
            )


def record_billing_event(
    tenant_id: str,
    type_: str,
    plan_code: str | None = None,
    amount_chf_cents: int | None = None,
    external_id: str | None = None,
) -> None:
    """Schreibt die kundensichtbare Historie (mandantengebunden via RLS)."""
    with tenant_tx(tenant_id) as conn:
        conn.execute(
            "INSERT INTO billing_events (tenant_id, type, plan_code, amount_chf_cents, external_id) "
            "VALUES (%s,%s,%s,%s,%s)",
            (tenant_id, type_, plan_code, amount_chf_cents, external_id),
        )
