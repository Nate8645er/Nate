"""E2E: signierter orders/paid-Webhook schaltet automatisch einen Mandanten
frei. Laeuft nur mit PLATFORM_TEST_DATABASE_URL."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os

import pytest

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)

SECRET = "test-shop-secret"


def _sign(body: bytes) -> str:
    return base64.b64encode(hmac.new(SECRET.encode(), body, hashlib.sha256).digest()).decode()


def _order(sku="plan-pro", email="kunde@example.ch", order_id=123):
    # order_id dient zugleich als Idempotenz-Kennung -> pro Test eigener Wert.
    return json.dumps(
        {"id": order_id, "email": email, "customer": {"first_name": "Kim"},
         "line_items": [{"sku": sku}]}
    ).encode()


def test_signed_webhook_provisions(client):
    body = _order()
    r = client.post(
        "/webhooks/shopify/orders-paid",
        content=body,
        headers={"X-Shopify-Hmac-Sha256": _sign(body), "Content-Type": "application/json"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "provisioned" and data["plan"] == "pro"
    assert data["tenant_id"]


def test_bad_signature_rejected(client):
    body = _order()
    r = client.post(
        "/webhooks/shopify/orders-paid",
        content=body,
        headers={"X-Shopify-Hmac-Sha256": "wrong", "Content-Type": "application/json"},
    )
    assert r.status_code == 401


def test_unknown_plan_sku_400(client):
    body = _order(sku="sticker", order_id=901)
    r = client.post(
        "/webhooks/shopify/orders-paid",
        content=body,
        headers={"X-Shopify-Hmac-Sha256": _sign(body), "Content-Type": "application/json"},
    )
    # SKU ohne 'plan-' -> kein Tarif erkannt -> 400.
    assert r.status_code == 400


def test_duplicate_order_provisions_only_once(client):
    body = _order(order_id=902, email="doppelt@example.ch")
    headers = {"X-Shopify-Hmac-Sha256": _sign(body), "Content-Type": "application/json"}

    first = client.post("/webhooks/shopify/orders-paid", content=body, headers=headers)
    assert first.json()["status"] == "provisioned"

    second = client.post("/webhooks/shopify/orders-paid", content=body, headers=headers)
    assert second.json()["status"] == "duplicate_ignored"

    # Es darf genau EIN Mandant fuer diese Bestellung existieren.
    import psycopg
    with psycopg.connect(DSN) as c:
        n = c.execute(
            "SELECT count(*) FROM users WHERE email = 'doppelt@example.ch'"
        ).fetchone()[0]
    assert n == 1


def test_missing_order_id_and_header_rejected_400(client):
    """Fail-closed: ohne X-Shopify-Webhook-Id UND ohne order.id ist keine
    Idempotenz moeglich -> ablehnen statt fail-open zu verarbeiten."""
    body = json.dumps(
        {"email": "keine-id@example.ch", "line_items": [{"sku": "plan-pro"}]}
    ).encode()
    r = client.post(
        "/webhooks/shopify/orders-paid",
        content=body,
        headers={"X-Shopify-Hmac-Sha256": _sign(body), "Content-Type": "application/json"},
    )
    assert r.status_code == 400


def test_oversized_body_rejected_413(client):
    huge = b"x" * 1_500_000
    r = client.post(
        "/webhooks/shopify/orders-paid",
        content=huge,
        headers={"X-Shopify-Hmac-Sha256": "irrelevant", "Content-Type": "application/octet-stream"},
    )
    assert r.status_code == 413


def test_invalid_order_does_not_burn_event_id(client):
    """Ein 400 darf die Ereignis-Kennung nicht verbrauchen: eine korrigierte
    Wiederzustellung mit derselben Kennung muss noch freischalten koennen."""
    bad = _order(sku="sticker", order_id=903)
    r1 = client.post(
        "/webhooks/shopify/orders-paid", content=bad,
        headers={"X-Shopify-Hmac-Sha256": _sign(bad), "Content-Type": "application/json"},
    )
    assert r1.status_code == 400

    good = _order(sku="plan-pro", order_id=903, email="korrigiert@example.ch")
    r2 = client.post(
        "/webhooks/shopify/orders-paid", content=good,
        headers={"X-Shopify-Hmac-Sha256": _sign(good), "Content-Type": "application/json"},
    )
    assert r2.status_code == 200 and r2.json()["status"] == "provisioned"
