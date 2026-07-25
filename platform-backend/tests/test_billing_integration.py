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


# --- Security-Review-Fixes: gezielt bewiesen ---------------------------------

def test_metadata_tenant_hijack_rejected(client, prov):
    """HOCH-1: metadata.tenant_id auf einen FREMDEN Mandanten (dessen E-Mail
    der Zahler nicht besitzt) darf nicht uebernommen werden. Der Kauf muss
    stattdessen einen NEUEN Mandanten anlegen statt den Fremden zu kapern."""
    prov("free")  # legt "T"/t@example.ch als Opfer-Mandant an
    import psycopg
    with psycopg.connect(DSN) as c:
        victim_id = c.execute(
            "SELECT id FROM tenants WHERE name = 'T' ORDER BY created_at DESC LIMIT 1"
        ).fetchone()[0]

    r = _post(client, _event("evt_hijack", "checkout.session.completed", {
        "customer": "cus_attacker", "subscription": "sub_attacker",
        "customer_details": {"email": "attacker@evil.example"},
        "metadata": {"plan_code": "business", "tenant_id": str(victim_id)},
    }))
    assert r.status_code == 200, r.text
    data = r.json()
    # Es wurde EIN NEUER Mandant angelegt, NICHT der Opfer-Mandant uebernommen.
    assert data["tenant_id"] != str(victim_id)

    with psycopg.connect(DSN) as c:
        victim = c.execute(
            "SELECT stripe_customer_id, plan_id FROM tenants WHERE id = %s", (victim_id,)
        ).fetchone()
    assert victim[0] is None, "Opfer-Mandant wurde faelschlich mit dem Angreifer-Kunden verknuepft"


def test_metadata_tenant_with_ownership_is_accepted(client, prov):
    """Legitimer Fall: E-Mail des Zahlers gehoert wirklich zu diesem Mandanten
    -> Verknuepfung wird akzeptiert (Upgrade eines bestehenden Kontos)."""
    prov("free")
    import psycopg
    with psycopg.connect(DSN) as c:
        tenant_id, owner_email = c.execute(
            "SELECT t.id, u.email FROM tenants t JOIN users u ON u.tenant_id = t.id "
            "WHERE t.name = 'T' ORDER BY t.created_at DESC LIMIT 1"
        ).fetchone()

    r = _post(client, _event("evt_legit_link", "checkout.session.completed", {
        "customer": "cus_legit", "subscription": "sub_legit",
        "customer_details": {"email": owner_email},
        "metadata": {"plan_code": "business", "tenant_id": str(tenant_id)},
    }))
    assert r.status_code == 200, r.text
    assert r.json()["tenant_id"] == str(tenant_id)

    with psycopg.connect(DSN) as c:
        st = c.execute(
            "SELECT stripe_customer_id, subscription_status FROM tenants WHERE id = %s", (tenant_id,)
        ).fetchone()
    assert st[0] == "cus_legit" and st[1] == "active"


def test_link_does_not_overwrite_existing_different_customer(client):
    """Zweite Verteidigungslinie: ist bereits ein ANDERER Stripe-Kunde
    verknuepft, darf ein zweiter Checkout mit derselben metadata.tenant_id
    diese Verknuepfung nicht ueberschreiben."""
    r1 = _post(client, _event("evt_first_link", "checkout.session.completed", {
        "customer": "cus_original", "subscription": "sub_original",
        "customer_details": {"email": "original@example.ch"},
        "metadata": {"plan_code": "starter"},
    }))
    tenant_id = r1.json()["tenant_id"]

    # Zweiter Versuch behauptet denselben Mandanten via Metadaten, aber mit
    # einer E-Mail, die (noch) nicht zu diesem Mandanten gehoert -> abgelehnt,
    # legt stattdessen einen neuen Mandanten an; der Original-Link bleibt.
    _post(client, _event("evt_second_link", "checkout.session.completed", {
        "customer": "cus_other", "subscription": "sub_other",
        "customer_details": {"email": "other@example.ch"},
        "metadata": {"plan_code": "pro", "tenant_id": tenant_id},
    }))

    import psycopg
    with psycopg.connect(DSN) as c:
        st = c.execute(
            "SELECT stripe_customer_id FROM tenants WHERE id = %s", (tenant_id,)
        ).fetchone()
    assert st[0] == "cus_original"


def test_admin_suspension_survives_invoice_paid(client):
    """MEDIUM: eine administrativ gesetzte Sperre (suspended_reason='admin')
    darf durch ein reguläres invoice.paid NICHT aufgehoben werden."""
    _post(client, _event("evt_admin1", "checkout.session.completed", {
        "customer": "cus_admin", "subscription": "sub_admin",
        "customer_details": {"email": "admin-case@example.ch"},
        "metadata": {"plan_code": "pro"},
    }))
    import psycopg
    with psycopg.connect(DSN, autocommit=True) as c:
        c.execute(
            "UPDATE tenants SET status='suspended', suspended_reason='admin' "
            "WHERE stripe_customer_id='cus_admin'"
        )

    _post(client, _event("evt_admin2", "invoice.paid", {"customer": "cus_admin", "amount_paid": 4900}))

    with psycopg.connect(DSN) as c:
        st = c.execute(
            "SELECT status, suspended_reason FROM tenants WHERE stripe_customer_id='cus_admin'"
        ).fetchone()
    assert st[0] == "suspended" and st[1] == "admin"


def test_billing_suspension_does_not_need_admin_reason(client):
    """Gegenprobe: eine NUR billing-bedingte Sperre wird durch invoice.paid
    normal wieder aufgehoben (Regressionsschutz gegen Ueberkorrektur)."""
    _post(client, _event("evt_bill1", "checkout.session.completed", {
        "customer": "cus_normal", "subscription": "sub_normal",
        "customer_details": {"email": "normal-case@example.ch"},
        "metadata": {"plan_code": "pro"},
    }))
    _post(client, _event("evt_bill2", "invoice.payment_failed", {"customer": "cus_normal", "amount_due": 4900}))
    _post(client, _event("evt_bill3", "invoice.paid", {"customer": "cus_normal", "amount_paid": 4900}))

    import psycopg
    with psycopg.connect(DSN) as c:
        st = c.execute(
            "SELECT status, suspended_reason FROM tenants WHERE stripe_customer_id='cus_normal'"
        ).fetchone()
    assert st[0] == "active" and st[1] is None


def test_missing_event_id_rejected_400(client):
    """LOW: ohne Ereignis-Kennung fail-closed ablehnen statt fail-open zu
    verarbeiten (verhindert doppelte Mandanten bei Replay ohne id)."""
    body = json.dumps({"type": "checkout.session.completed", "data": {"object": {}}}).encode()
    ts = int(time.time())
    sig = hmac.new(SECRET.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    r = client.post(
        "/webhooks/stripe", content=body,
        headers={"Stripe-Signature": f"t={ts},v1={sig}", "Content-Type": "application/json"},
    )
    assert r.status_code == 400


def test_oversized_body_rejected_413(client):
    """MEDIUM: unbegrenzte Bodies auf dem unauthentifizierten Webhook sind
    ein Speicher-DoS-Vektor; muessen VOR der Signaturpruefung abgewiesen werden."""
    huge = b"x" * 1_500_000  # ueber dem 1-MiB-Limit
    r = client.post(
        "/webhooks/stripe", content=huge,
        headers={"Stripe-Signature": "t=1,v1=irrelevant", "Content-Type": "application/octet-stream"},
    )
    assert r.status_code == 413
