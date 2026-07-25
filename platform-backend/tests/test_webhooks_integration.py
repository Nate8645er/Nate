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


def _order(sku="plan-pro", email="kunde@example.ch"):
    return json.dumps(
        {"id": 123, "email": email, "customer": {"first_name": "Kim"},
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
    body = _order(sku="sticker")
    r = client.post(
        "/webhooks/shopify/orders-paid",
        content=body,
        headers={"X-Shopify-Hmac-Sha256": _sign(body), "Content-Type": "application/json"},
    )
    # SKU ohne 'plan-' -> kein Tarif erkannt -> 400.
    assert r.status_code == 400
