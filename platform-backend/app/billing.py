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
import uuid as uuid_mod

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
    for s in sigs:
        # compare_digest wirft TypeError bei Nicht-ASCII-Kandidaten (Header
        # werden latin-1-dekodiert) — als Nicht-Treffer werten, nicht crashen.
        try:
            if hmac.compare_digest(expected, s):
                return True
        except TypeError:
            continue
    return False


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
    """Belegt das Event INNERHALB der uebergebenen Transaktion.

    Damit sind Belegung und die eigentliche Verarbeitung (z. B. Mandant
    anlegen, Abo-Zustand setzen) EIN Commit: bricht die Verarbeitung ab, wird
    auch die Belegung zurueckgerollt und eine Wiederzustellung greift korrekt.
    True = neu (und jetzt belegt), False = bereits verarbeitet.

    Ohne event_id ist keine Idempotenz moeglich — das wird hier als "bereits
    verarbeitet" (False) gewertet, also FAIL-CLOSED: lieber ein Event uebersehen
    (vom Betreiber manuell nachholbar) als durch Fail-Open versehentlich
    doppelte Mandanten anzulegen. Aufrufer sollten eine fehlende event_id aber
    schon vorher mit 400 ablehnen (siehe routes/billing.py, routes/webhooks.py).
    """
    if not event_id:
        log.warning("claim_event ohne event_id fuer provider=%s — als Duplikat behandelt", provider)
        return False
    row = conn.execute(
        "INSERT INTO processed_webhooks (provider, event_id) VALUES (%s, %s) "
        "ON CONFLICT (provider, event_id) DO NOTHING RETURNING event_id",
        (provider, event_id),
    ).fetchone()
    return row is not None


# --------------------------------------------------------------------------
# Mandanten-Zuordnung / Eigentumsnachweis
# --------------------------------------------------------------------------
def find_tenant_by_customer(customer_id: str) -> str | None:
    if not customer_id:
        return None
    with admin_tx() as conn:
        row = conn.execute(
            "SELECT id FROM tenants WHERE stripe_customer_id = %s", (customer_id,)
        ).fetchone()
    return str(row["id"]) if row else None


def resolve_metadata_tenant(raw_tenant_id, payer_email: str | None) -> str | None:
    """Prueft ein aus Checkout-Metadaten stammendes tenant_id, BEVOR es
    irgendetwas steuert. Ohne diese Pruefung koennte ein Angreifer, der
    metadata.tenant_id setzen kann, die Abrechnung eines fremden Mandanten
    uebernehmen (Security-Review, Befund HOCH-1).

    Akzeptiert nur, wenn:
      1. raw_tenant_id eine gueltige UUID ist, UND
      2. payer_email zu einem registrierten Nutzer GENAU dieses Mandanten
         gehoert (Eigentumsnachweis — RLS-gefiltert, kein Cross-Tenant-Read).
    """
    if not raw_tenant_id or not payer_email:
        return None
    try:
        tenant_id = str(uuid_mod.UUID(str(raw_tenant_id)))
    except (ValueError, AttributeError, TypeError):
        log.warning("metadata.tenant_id ist keine gueltige UUID: %r", raw_tenant_id)
        return None

    with tenant_tx(tenant_id) as conn:
        owns = conn.execute(
            "SELECT 1 FROM users WHERE email = %s", (payer_email,)
        ).fetchone()
    if owns is None:
        log.warning(
            "metadata.tenant_id abgelehnt (kein Eigentumsnachweis fuer %s): %s",
            payer_email, tenant_id,
        )
        return None
    return tenant_id


def link_stripe_customer(tenant_id: str, customer_id: str, subscription_id: str | None, conn=None) -> None:
    """Verknuepft die Stripe-Customer-ID nur, wenn noch keine ANDERE verknuepft
    ist (verhindert Ueberschreiben/Kapern einer bestehenden Verknuepfung —
    zweite Verteidigungslinie neben resolve_metadata_tenant)."""
    def _do(c):
        c.execute(
            "UPDATE tenants SET stripe_customer_id = %s, "
            "stripe_subscription_id = COALESCE(%s, stripe_subscription_id) "
            "WHERE id = %s AND (stripe_customer_id IS NULL OR stripe_customer_id = %s)",
            (customer_id or None, subscription_id, tenant_id, customer_id or None),
        )
    if conn is not None:
        _do(conn)
    else:
        with admin_tx() as c:
            _do(c)


def store_checkout_handoff(stripe_session_id: str, tenant_id: str, api_key_clear: str, conn=None) -> None:
    """Legt den einmalig abrufbaren Abholschein fuer den frisch erzeugten
    Klartext-API-Key ab -- die Erfolgsseite nach dem Stripe-Checkout holt ihn
    per stripe_session_id ab (claim_checkout_handoff), damit der Kunde direkt
    loslegen kann statt seinen eigenen API-Key suchen zu muessen."""
    def _do(c):
        c.execute(
            "INSERT INTO checkout_handoffs (stripe_session_id, tenant_id, api_key_clear) "
            "VALUES (%s,%s,%s) ON CONFLICT (stripe_session_id) DO NOTHING",
            (stripe_session_id, tenant_id, api_key_clear),
        )
    if conn is not None:
        _do(conn)
    else:
        with admin_tx() as c:
            _do(c)


# Abholschein gilt nur kurz -- der Kunde landet direkt nach dem Checkout auf
# der Erfolgsseite, nicht Stunden spaeter. Begrenzt die Zeit, in der ein
# geleakter Session-Link (Browser-Verlauf, geteilter Bildschirm) noch etwas
# wert waere.
_CHECKOUT_HANDOFF_TTL_MINUTES = 60


def claim_checkout_handoff(stripe_session_id: str) -> dict | None:
    """Liefert (tenant_id, api_key_clear) genau EINMAL und loescht den
    Abholschein danach unwiderruflich -- weder erneuter Abruf noch
    abgelaufene Scheine liefern etwas."""
    with admin_tx() as conn:
        # "%s minutes" innerhalb eines String-Literals wuerde psycopg NICHT
        # als Bind-Parameter erkennen (Platzhalter in Anfuehrungszeichen
        # werden nicht gebunden) -- deshalb ueber Multiplikation mit einem
        # festen Intervall-Literal, ausserhalb jeder Quotes.
        row = conn.execute(
            "DELETE FROM checkout_handoffs "
            "WHERE stripe_session_id = %s "
            "AND created_at > now() - (%s * interval '1 minute') "
            "RETURNING tenant_id, api_key_clear",
            (stripe_session_id, _CHECKOUT_HANDOFF_TTL_MINUTES),
        ).fetchone()
    if row is None:
        return None
    return {"tenant_id": str(row["tenant_id"]), "api_key": row["api_key_clear"]}


def apply_subscription_state(
    tenant_id: str,
    plan_code: str | None,
    subscription_status: str,
    current_period_end=None,
    subscription_id: str | None = None,
    conn=None,
) -> None:
    """Setzt Tarif + Abo-Zustand am Mandanten. Ein nicht-aktives Abo sperrt den
    Mandanten (auth.py -> 403), ein wieder aktives entsperrt ihn — AUSSER der
    Mandant ist administrativ gesperrt (suspended_reason='admin'): das darf ein
    regulaeres invoice.paid nicht aufheben (Security-Review, Befund MEDIUM)."""
    def _do(c):
        plan_id = None
        if plan_code:
            plan = c.execute("SELECT id FROM plans WHERE code = %s", (plan_code,)).fetchone()
            if plan is None:
                log.warning("Unbekannter Tarif '%s' im Abo-Event", plan_code)
            else:
                plan_id = plan["id"]

        current = c.execute(
            "SELECT suspended_reason FROM tenants WHERE id = %s", (tenant_id,)
        ).fetchone()
        current_reason = current["suspended_reason"] if current else None

        if subscription_status in ACTIVE_STATUSES:
            if current_reason == "admin":
                new_status, new_reason = "suspended", "admin"  # admin-Sperre bleibt bestehen
            else:
                new_status, new_reason = "active", None
        else:
            new_status, new_reason = "suspended", "billing"

        if plan_id is not None:
            c.execute(
                "UPDATE tenants SET plan_id = %s, subscription_status = %s, status = %s, "
                "suspended_reason = %s, current_period_end = %s, "
                "stripe_subscription_id = COALESCE(%s, stripe_subscription_id) WHERE id = %s",
                (plan_id, subscription_status, new_status, new_reason, current_period_end,
                 subscription_id, tenant_id),
            )
        else:
            c.execute(
                "UPDATE tenants SET subscription_status = %s, status = %s, suspended_reason = %s, "
                "current_period_end = %s, stripe_subscription_id = COALESCE(%s, stripe_subscription_id) "
                "WHERE id = %s",
                (subscription_status, new_status, new_reason, current_period_end,
                 subscription_id, tenant_id),
            )

    if conn is not None:
        _do(conn)
    else:
        with admin_tx() as c:
            _do(c)


def record_billing_event(
    tenant_id: str,
    type_: str,
    plan_code: str | None = None,
    amount_chf_cents: int | None = None,
    external_id: str | None = None,
    conn=None,
) -> None:
    """Schreibt die kundensichtbare Historie (mandantengebunden via RLS)."""
    if conn is not None:
        # Gemeinsame Transaktion: Mandantenkontext auf DIESER Verbindung setzen
        # (wie in provisioning.py), damit die WITH-CHECK-Policy erfuellt ist.
        conn.execute("SELECT set_config('app.current_tenant', %s, true)", (str(tenant_id),))
        conn.execute(
            "INSERT INTO billing_events (tenant_id, type, plan_code, amount_chf_cents, external_id) "
            "VALUES (%s,%s,%s,%s,%s)",
            (tenant_id, type_, plan_code, amount_chf_cents, external_id),
        )
        return
    with tenant_tx(tenant_id) as c:
        c.execute(
            "INSERT INTO billing_events (tenant_id, type, plan_code, amount_chf_cents, external_id) "
            "VALUES (%s,%s,%s,%s,%s)",
            (tenant_id, type_, plan_code, amount_chf_cents, external_id),
        )
