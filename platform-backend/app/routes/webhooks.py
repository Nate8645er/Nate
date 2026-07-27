"""Store-Webhook (Produkt B -> A): Shopify `orders/paid` schaltet nach einem
Kauf automatisch einen Mandanten frei (Master-Prompt 4.2).

Sicherheit: Shopify signiert jeden Webhook mit HMAC-SHA256 ueber den ROHEN
Body (Header X-Shopify-Hmac-Sha256, base64). Wir verifizieren konstant-Zeit
gegen SHOPIFY_WEBHOOK_SECRET, bevor irgendetwas passiert.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os

from fastapi import APIRouter, HTTPException, Request

from ..billing import claim_event
from ..db import admin_tx
from ..http_limits import read_bounded_body
from ..provisioning import provision_tenant

router = APIRouter()
log = logging.getLogger("platform.webhooks")


def verify_shopify_hmac(raw_body: bytes, header_hmac: str, secret: str) -> bool:
    """Konstant-Zeit-Vergleich der Shopify-Signatur."""
    if not secret or not header_hmac:
        return False
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(expected, header_hmac)


def plan_code_from_order(order: dict) -> str | None:
    """Ermittelt den gekauften Tarif aus den line_items. Konvention: die SKU
    lautet 'plan-<code>' (z.B. 'plan-pro')."""
    for item in order.get("line_items", []) or []:
        sku = (item.get("sku") or "").strip().lower()
        if sku.startswith("plan-"):
            return sku[len("plan-"):]
    return None


def email_from_order(order: dict) -> str | None:
    return order.get("email") or (order.get("customer") or {}).get("email")


@router.post("/webhooks/shopify/orders-paid")
async def orders_paid(request: Request):
    raw = await read_bounded_body(request)
    header_hmac = request.headers.get("X-Shopify-Hmac-Sha256", "")
    secret = os.environ.get("SHOPIFY_WEBHOOK_SECRET", "")

    if not verify_shopify_hmac(raw, header_hmac, secret):
        # 401 -> Shopify wertet es als Fehlschlag; wir wollen keine unsignierten
        # Aufrufe verarbeiten.
        raise HTTPException(status_code=401, detail="Ungueltige Signatur")

    try:
        order = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Ungueltiger Body")

    # Erst validieren: ein unbrauchbarer Auftrag soll die Ereignis-Kennung nicht
    # verbrauchen (sonst wuerde eine korrigierte Wiederzustellung verworfen).
    plan_code = plan_code_from_order(order)
    email = email_from_order(order)
    if not plan_code or not email:
        log.warning("orders/paid ohne Tarif-SKU oder E-Mail: order=%s", order.get("id"))
        raise HTTPException(status_code=400, detail="Kein Tarif (plan-<code>) oder keine E-Mail im Auftrag")

    # Idempotenz: Shopify stellt Webhooks mehrfach zu. Belegung und Anlage
    # laufen in EINER Transaktion — bricht die Anlage ab, wird auch die Belegung
    # zurueckgerollt und die Wiederzustellung greift korrekt.
    event_id = request.headers.get("X-Shopify-Webhook-Id") or str(order.get("id") or "")
    if not event_id:
        # Fail-closed: ohne Kennung keine Idempotenz moeglich (sonst koennte
        # jede Wiederzustellung einen weiteren Mandanten anlegen).
        raise HTTPException(status_code=400, detail="Auftrag ohne Kennung")
    tenant_name = order.get("customer", {}).get("first_name") or email.split("@")[0]

    with admin_tx() as conn:
        if not claim_event(conn, "shopify", event_id):
            log.info("orders/paid Wiederholung ignoriert: %s", event_id)
            return {"status": "duplicate_ignored", "event": event_id}
        result = provision_tenant(
            tenant_name=tenant_name, owner_email=email, plan_code=plan_code, conn=conn
        )
    log.info("Mandant via Store-Kauf freigeschaltet: tenant=%s plan=%s", result["tenant_id"], plan_code)

    # Bewusst offene Luecke (bestand bereits vor der Session-Cookie-
    # Umstellung, ist keine neue Regression): der Kunde hat im
    # Shopify-Checkout kein Passwort vergeben, und anders als beim
    # Stripe-Checkout (app/routes/billing.py) gibt es hier keinen
    # Live-Redirect auf eine eigene Erfolgsseite, ueber den eine frisch
    # erzeugte Session per Cookie ausgeliefert werden koennte.
    # provision_tenant() legt den Mandanten deshalb OHNE Passwort an -- aber
    # (Sicherheits-Fix, siehe app/provisioning.py) SEHR WOHL mit sofortigem
    # `user_directory`-Eintrag. Der Kunde hat also KEINEN Auto-Login wie bei
    # Stripe, aber einen regulaeren Weg zurueck: `/v1/auth/signup` mit
    # genau dieser E-Mail beansprucht das bestehende Konto und setzt das
    # erste Passwort (`_claim_existing_account` in `app/routes/auth.py`),
    # statt mit 409 abgelehnt zu werden oder (der urspruengliche Fund) einem
    # Angreifer einen konkurrierenden Mandanten fuer dieselbe E-Mail zu
    # erlauben. Ein direkter Live-Redirect mit Auto-Login waere komfortabler,
    # ist aber nicht Teil dieser Runde.
    return {"status": "provisioned", "tenant_id": result["tenant_id"], "plan": plan_code}
