"""E2E der Abrechnung gegen eine echte Postgres-DB: Kauf -> Tarifwechsel ->
Zahlungsausfall (sperrt) -> Zahlung (entsperrt) -> Kuendigung. Plus Idempotenz.

Laeuft nur mit PLATFORM_TEST_DATABASE_URL.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time

import pytest

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)

SECRET = "whsec_test_integration"


def _post(client, event: dict):
    body = json.dumps(event).encode()
    ts = int(time.time())
    sig = hmac.new(SECRET.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return client.post(
        "/webhooks/stripe",
        content=body,
        headers={"Stripe-Signature": f"t={ts},v1={sig}", "Content-Type": "application/json"},
    )


def _event(eid, etype, obj):
    return {"id": eid, "type": etype, "data": {"object": obj}}


def test_checkout_provisions_and_links_customer(client):
    r = _post(client, _event("evt_1", "checkout.session.completed", {
        "customer": "cus_1", "subscription": "sub_1",
        "customer_details": {"email": "kauf@example.ch"},
        "metadata": {"plan_code": "pro"},
    }))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "provisioned"
    assert r.json()["plan"] == "pro"


def test_duplicate_event_is_ignored(client):
    ev = _event("evt_dup", "checkout.session.completed", {
        "customer": "cus_dup", "subscription": "sub_dup",
        "customer_details": {"email": "dup@example.ch"},
        "metadata": {"plan_code": "starter"},
    })
    first = _post(client, ev)
    assert first.json()["status"] == "provisioned"
    second = _post(client, ev)
    assert second.json()["status"] == "duplicate_ignored"


def test_bad_signature_rejected(client):
    body = json.dumps(_event("evt_bad", "invoice.paid", {})).encode()
    r = client.post(
        "/webhooks/stripe",
        content=body,
        headers={"Stripe-Signature": "t=1,v1=deadbeef", "Content-Type": "application/json"},
    )
    assert r.status_code == 401


def test_lifecycle_upgrade_suspend_resume_cancel(client):
    # Kauf (Starter)
    _post(client, _event("evt_l1", "checkout.session.completed", {
        "customer": "cus_life", "subscription": "sub_life",
        "customer_details": {"email": "life@example.ch"},
        "metadata": {"plan_code": "starter"},
    }))

    # Upgrade auf Business
    r = _post(client, _event("evt_l2", "customer.subscription.updated", {
        "id": "sub_life", "customer": "cus_life", "status": "active",
        "metadata": {"plan_code": "business"},
        "current_period_end": int(time.time()) + 86400,
    }))
    assert r.json()["plan"] == "business"

    # Zahlungsausfall -> Mandant gesperrt
    r = _post(client, _event("evt_l3", "invoice.payment_failed", {
        "customer": "cus_life", "amount_due": 14900,
    }))
    assert r.json()["status"] == "payment_failed"
    import psycopg
    with psycopg.connect(DSN) as c:
        st = c.execute(
            "SELECT status, subscription_status FROM tenants WHERE stripe_customer_id='cus_life'"
        ).fetchone()
    assert st[0] == "suspended" and st[1] == "past_due"

    # Zahlung -> wieder aktiv
    _post(client, _event("evt_l4", "invoice.paid", {"customer": "cus_life", "amount_paid": 14900}))
    with psycopg.connect(DSN) as c:
        st = c.execute(
            "SELECT status FROM tenants WHERE stripe_customer_id='cus_life'"
        ).fetchone()
    assert st[0] == "active"

    # Kuendigung -> gesperrt
    _post(client, _event("evt_l5", "customer.subscription.deleted", {
        "id": "sub_life", "customer": "cus_life",
    }))
    with psycopg.connect(DSN) as c:
        st = c.execute(
            "SELECT status, subscription_status FROM tenants WHERE stripe_customer_id='cus_life'"
        ).fetchone()
    assert st[0] == "suspended" and st[1] == "canceled"


def test_suspended_tenant_is_locked_out(client, prov):
    key = prov("free")
    h = {"Authorization": "Bearer " + key}
    assert client.get("/v1/models", headers=h).status_code == 200

    # Mandanten sperren (wie nach Zahlungsausfall)
    import psycopg
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(
            "UPDATE tenants SET status='suspended' WHERE id = ("
            "  SELECT tenant_id FROM api_keys ORDER BY created_at DESC LIMIT 1)"
        )
    assert client.get("/v1/models", headers=h).status_code == 403


def test_billing_overview(client, prov):
    key = prov("pro")
    h = {"Authorization": "Bearer " + key}
    r = client.get("/v1/billing", headers=h)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["plan"] == "pro"
    assert data["currency"] == "CHF" and data["vat_note"] == "inkl. MwSt"
    assert data["usage"]["limit"] > 0
    assert isinstance(data["history"], list)


def test_unknown_customer_event_ignored(client):
    r = _post(client, _event("evt_unknown", "invoice.paid", {"customer": "cus_nope"}))
    assert r.json()["status"] == "ignored_unknown_customer"
