"""Abrechnung (Phase 4):
  POST /webhooks/stripe  — Abo-Ereignisse: Kauf, Tarifwechsel, Zahlung, Kuendigung
  GET  /v1/billing       — Kundenansicht: Tarif, Abo-Zustand, Verbrauch, Historie

Sicherheitsprinzip (Security-Review): jedes Ereignis, das etwas ANLEGT oder
ZUSTAND AENDERT, belegt seine Idempotenz-Kennung und fuehrt die Aenderung in
EINER Transaktion aus. Validierung (Tarif/E-Mail bekannt?) passiert VOR dem
Belegen, damit ein abgelehntes Event (400) die Kennung nicht verbraucht.
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request

from ..auth import Principal, require_principal
from ..billing import (
    apply_subscription_state,
    claim_event,
    find_tenant_by_customer,
    link_stripe_customer,
    plan_code_from_event,
    record_billing_event,
    resolve_metadata_tenant,
    verify_stripe_signature,
)
from ..db import admin_tx, tenant_tx
from ..http_limits import read_bounded_body
from ..provisioning import provision_tenant

router = APIRouter()
log = logging.getLogger("platform.billing.routes")


def _ts(value) -> dt.datetime | None:
    if not value:
        return None
    try:
        return dt.datetime.fromtimestamp(int(value), tz=dt.timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def _email_from_session(obj: dict) -> str | None:
    return (
        obj.get("customer_email")
        or ((obj.get("customer_details") or {}).get("email"))
        or None
    )


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    raw = await read_bounded_body(request)
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    if not verify_stripe_signature(raw, request.headers.get("Stripe-Signature", ""), secret):
        raise HTTPException(status_code=401, detail="Ungueltige Signatur")

    try:
        event = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Ungueltiger Body")

    event_id = event.get("id", "")
    etype = event.get("type", "")
    obj = ((event.get("data") or {}).get("object")) or {}
    customer_id = obj.get("customer") or ""

    if not event_id:
        # Fail-closed: ohne Kennung keine Idempotenz moeglich. Lieber ablehnen
        # (Stripe stellt praktisch immer eine id) als riskieren, ein Replay
        # doppelt zu verarbeiten.
        raise HTTPException(status_code=400, detail="Event ohne Kennung")

    tenant_id = find_tenant_by_customer(customer_id)

    # ---- Kauf abgeschlossen -------------------------------------------------
    if etype == "checkout.session.completed":
        plan_code = plan_code_from_event(obj)
        subscription_id = obj.get("subscription") or None
        email = _email_from_session(obj)

        if tenant_id is None:
            # Nur akzeptieren, wenn Eigentum am Ziel-Mandanten nachgewiesen ist
            # (gueltige UUID + payer_email gehoert zu einem Nutzer dieses
            # Mandanten) — verhindert Uebernahme eines fremden Mandanten ueber
            # frei waehlbare Checkout-Metadaten.
            meta_tenant = (obj.get("metadata") or {}).get("tenant_id")
            if meta_tenant:
                tenant_id = resolve_metadata_tenant(meta_tenant, email)

        if tenant_id is None:
            # Neukauf ohne bestehenden/nachgewiesenen Mandanten -> freischalten.
            # Validieren BEVOR die Ereignis-Kennung belegt wird.
            if not email or not plan_code:
                log.warning("checkout.session.completed ohne E-Mail/Tarif: %s", event_id)
                raise HTTPException(status_code=400, detail="Kein Tarif oder keine E-Mail")

            with admin_tx() as conn:
                if not claim_event(conn, "stripe", event_id):
                    return {"status": "duplicate_ignored", "event": event_id}
                result = provision_tenant(
                    tenant_name=email.split("@")[0], owner_email=email,
                    plan_code=plan_code, conn=conn,
                )
                new_tenant_id = result["tenant_id"]
                link_stripe_customer(new_tenant_id, customer_id, subscription_id, conn=conn)
                apply_subscription_state(
                    new_tenant_id, plan_code, "active", subscription_id=subscription_id, conn=conn
                )
                record_billing_event(
                    new_tenant_id, "subscription_started", plan_code,
                    external_id=event_id, conn=conn,
                )
            return {"status": "provisioned", "tenant_id": new_tenant_id, "plan": plan_code}

        # Bestehender/nachgewiesener Mandant -> verknuepfen + aktivieren.
        with admin_tx() as conn:
            if not claim_event(conn, "stripe", event_id):
                return {"status": "duplicate_ignored", "event": event_id}
            link_stripe_customer(tenant_id, customer_id, subscription_id, conn=conn)
            apply_subscription_state(
                tenant_id, plan_code, "active", subscription_id=subscription_id, conn=conn
            )
            record_billing_event(
                tenant_id, "subscription_started", plan_code, external_id=event_id, conn=conn
            )
        return {"status": "provisioned", "tenant_id": tenant_id, "plan": plan_code}

    # Ab hier ist ein bekannter Mandant noetig — ohne Zuordnung nicht belegen,
    # damit eine spaetere Zustellung (Mandant dann bekannt) noch greift.
    if tenant_id is None:
        log.info("Stripe-Event %s ohne zugeordneten Mandanten (customer=%s)", etype, customer_id)
        return {"status": "ignored_unknown_customer", "event": event_id}

    # ---- Abo geaendert / gekuendigt -----------------------------------------
    if etype in {"customer.subscription.created", "customer.subscription.updated"}:
        plan_code = plan_code_from_event(obj)
        status = obj.get("status", "active")
        with admin_tx() as conn:
            if not claim_event(conn, "stripe", event_id):
                return {"status": "duplicate_ignored", "event": event_id}
            apply_subscription_state(
                tenant_id, plan_code, status,
                current_period_end=_ts(obj.get("current_period_end")),
                subscription_id=obj.get("id"), conn=conn,
            )
            record_billing_event(tenant_id, "plan_changed", plan_code, external_id=event_id, conn=conn)
        return {"status": "updated", "tenant_id": tenant_id, "plan": plan_code}

    if etype == "customer.subscription.deleted":
        with admin_tx() as conn:
            if not claim_event(conn, "stripe", event_id):
                return {"status": "duplicate_ignored", "event": event_id}
            apply_subscription_state(tenant_id, None, "canceled", subscription_id=obj.get("id"), conn=conn)
            record_billing_event(tenant_id, "subscription_cancelled", external_id=event_id, conn=conn)
        return {"status": "cancelled", "tenant_id": tenant_id}

    # ---- Zahlungen ----------------------------------------------------------
    if etype == "invoice.paid":
        with admin_tx() as conn:
            if not claim_event(conn, "stripe", event_id):
                return {"status": "duplicate_ignored", "event": event_id}
            apply_subscription_state(tenant_id, None, "active", conn=conn)
            record_billing_event(
                tenant_id, "invoice_paid", amount_chf_cents=obj.get("amount_paid"),
                external_id=event_id, conn=conn,
            )
        return {"status": "invoice_paid", "tenant_id": tenant_id}

    if etype == "invoice.payment_failed":
        with admin_tx() as conn:
            if not claim_event(conn, "stripe", event_id):
                return {"status": "duplicate_ignored", "event": event_id}
            apply_subscription_state(tenant_id, None, "past_due", conn=conn)  # sperrt den Mandanten
            record_billing_event(
                tenant_id, "payment_failed", amount_chf_cents=obj.get("amount_due"),
                external_id=event_id, conn=conn,
            )
        return {"status": "payment_failed", "tenant_id": tenant_id}

    return {"status": "ignored", "event": event_id, "type": etype}


@router.get("/v1/billing")
async def billing_overview(principal: Principal = Depends(require_principal)):
    """Kundenansicht: Tarif, Abo-Zustand, Monatsverbrauch, Abrechnungs-Historie."""
    with admin_tx() as conn:
        t = conn.execute(
            "SELECT t.name, t.status, t.subscription_status, t.current_period_end, "
            "       p.code AS plan_code, p.price_chf_cents, p.monthly_token_limit "
            "FROM tenants t JOIN plans p ON p.id = t.plan_id WHERE t.id = %s",
            (principal.tenant_id,),
        ).fetchone()
    if t is None:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")

    with tenant_tx(principal.tenant_id) as conn:
        used = conn.execute(
            "SELECT COALESCE(SUM(tokens_in + tokens_out), 0) AS used FROM usage_events "
            "WHERE tenant_id = %s AND ts >= date_trunc('month', now())",
            (principal.tenant_id,),
        ).fetchone()["used"]
        history = conn.execute(
            "SELECT type, plan_code, amount_chf_cents, occurred_at FROM billing_events "
            "ORDER BY occurred_at DESC LIMIT 50"
        ).fetchall()

    limit = int(t["monthly_token_limit"])
    return {
        "tenant": t["name"],
        "plan": t["plan_code"],
        "price_chf": round(int(t["price_chf_cents"]) / 100, 2),
        "currency": "CHF",
        "vat_note": "inkl. MwSt",
        "account_status": t["status"],
        "subscription_status": t["subscription_status"],
        "current_period_end": t["current_period_end"].isoformat() if t["current_period_end"] else None,
        "usage": {
            "tokens_total": int(used),
            "limit": limit,
            "remaining": max(0, limit - int(used)),
            "percent": round(min(100.0, (int(used) / limit * 100) if limit else 0.0), 1),
        },
        "history": [
            {
                "type": h["type"],
                "plan": h["plan_code"],
                "amount_chf": round(h["amount_chf_cents"] / 100, 2) if h["amount_chf_cents"] is not None else None,
                "occurred_at": h["occurred_at"].isoformat(),
            }
            for h in history
        ],
    }
