"""Beweist die Onboarding-Luecke ist wirklich geschlossen: nach einem
Stripe-Kauf bekommt der Kunde seinen API-Key ueber die Checkout-Session-ID
(wie sie Stripe per ?session_id=... auf die success_url legt) -- ohne ihn
manuell suchen oder anfordern zu muessen. Gegen eine echte Postgres-DB."""
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


def _post_webhook(client, event: dict):
    body = json.dumps(event).encode()
    ts = int(time.time())
    sig = hmac.new(SECRET.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return client.post(
        "/webhooks/stripe",
        content=body,
        headers={"Stripe-Signature": f"t={ts},v1={sig}", "Content-Type": "application/json"},
    )


def _checkout_event(eid, session_id, customer, email, plan):
    return {
        "id": eid,
        "type": "checkout.session.completed",
        "data": {"object": {
            "id": session_id,
            "customer": customer,
            "subscription": f"sub_{session_id}",
            "customer_details": {"email": email},
            "metadata": {"plan_code": plan},
        }},
    }


def test_new_purchase_key_can_be_claimed_via_session_id(client):
    r = _post_webhook(client, _checkout_event(
        "evt_h1", "cs_test_h1", "cus_h1", "handoff1@example.ch", "starter",
    ))
    assert r.status_code == 200, r.text
    tenant_id = r.json()["tenant_id"]

    claim = client.get("/v1/checkout/cs_test_h1/claim")
    assert claim.status_code == 200, claim.text
    body = claim.json()
    assert body["tenant_id"] == tenant_id
    assert body["api_key"].startswith("pk_")

    # Der geclaimte Key funktioniert wirklich als Login.
    h = {"Authorization": "Bearer " + body["api_key"]}
    me = client.get("/v1/usage", headers=h)
    assert me.status_code == 200


def test_claim_is_single_use(client):
    _post_webhook(client, _checkout_event(
        "evt_h2", "cs_test_h2", "cus_h2", "handoff2@example.ch", "pro",
    ))
    first = client.get("/v1/checkout/cs_test_h2/claim")
    assert first.status_code == 200

    second = client.get("/v1/checkout/cs_test_h2/claim")
    assert second.status_code == 404


def test_unknown_session_id_is_404(client):
    r = client.get("/v1/checkout/cs_does_not_exist/claim")
    assert r.status_code == 404


def test_claim_requires_no_authentication(client):
    """Bewusst: der Kunde hat zu diesem Zeitpunkt noch keinen API-Key --
    dieser Endpunkt darf keinen Principal/Bearer-Header verlangen."""
    _post_webhook(client, _checkout_event(
        "evt_h3", "cs_test_h3", "cus_h3", "handoff3@example.ch", "free",
    ))
    r = client.get("/v1/checkout/cs_test_h3/claim")  # keine Authorization-Header
    assert r.status_code == 200
