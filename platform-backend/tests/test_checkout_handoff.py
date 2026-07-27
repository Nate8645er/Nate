"""Beweist die Onboarding-Luecke ist wirklich geschlossen: nach einem
Stripe-Kauf wird der Kunde ueber die Checkout-Session-ID (wie sie Stripe per
?session_id=... auf die success_url legt) automatisch per Session-Cookie
angemeldet -- ohne einen Schluessel manuell suchen, kopieren oder anfordern
zu muessen. Gegen eine echte Postgres-DB."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time

import pytest

from app.ratelimit import checkout_claim_limiter

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)

SECRET = "whsec_test_integration"


@pytest.fixture(autouse=True)
def _reset_claim_limiter():
    checkout_claim_limiter.reset()
    yield
    checkout_claim_limiter.reset()


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


def test_new_purchase_can_be_claimed_via_session_id(client):
    r = _post_webhook(client, _checkout_event(
        "evt_h1", "cs_test_h1", "cus_h1", "handoff1@example.ch", "starter",
    ))
    assert r.status_code == 200, r.text
    tenant_id = r.json()["tenant_id"]

    claim = client.get("/v1/checkout/cs_test_h1/claim")
    assert claim.status_code == 200, claim.text
    body = claim.json()
    assert body["tenant_id"] == tenant_id
    # Kein API-Key mehr im Body -- die Anmeldung laeuft ausschliesslich ueber
    # das per Set-Cookie ausgelieferte Session-Cookie.
    assert "api_key" not in body

    # Das Cookie wurde wirklich gesetzt und authentifiziert sofort (gleicher
    # Client, httpx uebernimmt Set-Cookie automatisch in sein Cookie-Jar).
    me = client.get("/v1/usage")
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
    """Bewusst: der Kunde hat zu diesem Zeitpunkt noch keine Session --
    dieser Endpunkt darf keinen Principal/Session-Cookie verlangen, um
    ERREICHT zu werden (er LIEFERT die Session ja erst per Set-Cookie)."""
    _post_webhook(client, _checkout_event(
        "evt_h3", "cs_test_h3", "cus_h3", "handoff3@example.ch", "free",
    ))
    r = client.get("/v1/checkout/cs_test_h3/claim")  # kein Cookie vorhanden
    assert r.status_code == 200


def test_claim_endpoint_is_rate_limited(client, monkeypatch):
    """Security-Review Punkt B: anders als Login/Signup hatte dieser
    unauthentifizierte, schreibende Endpunkt bisher KEIN Rate-Limiting --
    jetzt derselbe IP-Limiter-Mechanismus wie beim Login (app/ratelimit.py)."""
    monkeypatch.setattr(checkout_claim_limiter, "max_calls", 2)

    # Zwei Aufrufe passieren den Limiter (scheitern danach am unbekannten
    # Session-ID mit 404 -> beweist, dass sie den Limiter durchlaufen haben).
    for _ in range(2):
        r = client.get("/v1/checkout/cs_does_not_exist_ratelimit/claim")
        assert r.status_code == 404

    # Der dritte wird VOM LIMITER abgewiesen, bevor ueberhaupt nachgeschaut wird.
    r3 = client.get("/v1/checkout/cs_does_not_exist_ratelimit/claim")
    assert r3.status_code == 429
    assert "Retry-After" in r3.headers
