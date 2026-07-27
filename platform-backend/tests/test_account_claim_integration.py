"""Regressionstests fuer den kritischen Sicherheitsfund (Security-Review):
`provision_tenant()` legte bei passwortlosen Stripe-/Shopify-Kaeufen KEINEN
`user_directory`-Eintrag an -- der 409-Doppelregistrierungs-Schutz in
`/v1/auth/signup` griff deshalb nicht fuer diese E-Mail. Ein Angreifer, der
nur die E-Mail-Adresse eines zahlenden Kunden kannte, konnte sich per Signup
mit GENAU dieser E-Mail registrieren und die E-Mail auf einen eigenen,
neuen Mandanten umbiegen -- der echte Kunde verlor dauerhaft den Zugriff auf
sein eigenes Konto, sobald seine Session ablief.

Fix: `provision_tenant()` reserviert die E-Mail jetzt IMMER sofort in
`user_directory` (app/provisioning.py); `/v1/auth/signup` erkennt eine
bereits reservierte, aber passwortlose E-Mail und laesst den echten
Eigentuemer sein erstes Passwort auf dem BESTEHENDEN Konto setzen
("Konto beanspruchen", `_claim_existing_account` in app/routes/auth.py)
statt einen neuen, konkurrierenden Mandanten anzulegen.

Diese drei Tests beweisen genau das, gegen eine echte Postgres-DB."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time

import psycopg
import pytest

from app.ratelimit import signup_limiter, signup_limiter_email

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)

SECRET = "whsec_test_integration"


@pytest.fixture(autouse=True)
def _reset_limiters():
    for lim in (signup_limiter, signup_limiter_email):
        lim.reset()
    yield
    for lim in (signup_limiter, signup_limiter_email):
        lim.reset()


def _post_stripe_webhook(client, event: dict):
    body = json.dumps(event).encode()
    ts = int(time.time())
    sig = hmac.new(SECRET.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return client.post(
        "/webhooks/stripe",
        content=body,
        headers={"Stripe-Signature": f"t={ts},v1={sig}", "Content-Type": "application/json"},
    )


def _checkout_completed(eid, customer, email, plan):
    return {
        "id": eid,
        "type": "checkout.session.completed",
        "data": {"object": {
            "customer": customer,
            "subscription": f"sub_{customer}",
            "customer_details": {"email": email},
            "metadata": {"plan_code": plan},
        }},
    }


def test_passwordless_stripe_signup_gets_user_directory_entry_immediately(client):
    """Kern des Fundes: ein per Stripe (ohne Passwort) provisionierter Nutzer
    muss SOFORT einen `user_directory`-Eintrag haben -- vorher war das
    genau NICHT der Fall (nur wenn `password` uebergeben wurde)."""
    r = _post_stripe_webhook(client, _checkout_completed(
        "evt_claim_dir1", "cus_claim_dir1", "claimdir1@example.ch", "pro",
    ))
    assert r.status_code == 200, r.text
    tenant_id = r.json()["tenant_id"]

    with psycopg.connect(DSN) as c:
        row = c.execute(
            "SELECT tenant_id, user_id FROM user_directory WHERE email_lower = %s",
            ("claimdir1@example.ch",),
        ).fetchone()
    assert row is not None, (
        "Kritischer Fund: passwortlos provisionierter Stripe-Nutzer hatte "
        "keinen user_directory-Eintrag -- 409-Doppelregistrierungs-Schutz "
        "griff nicht."
    )
    assert str(row[0]) == tenant_id

    # Der zugehoerige users-Eintrag hat (wie erwartet) noch KEIN Passwort --
    # der Kunde hat im Checkout keins vergeben.
    with psycopg.connect(DSN) as c:
        pw_hash = c.execute(
            "SELECT password_hash FROM users WHERE id = %s", (row[1],)
        ).fetchone()[0]
    assert pw_hash is None


def test_attacker_cannot_hijack_paying_customers_email_via_signup(client):
    """Der eigentliche Angriff aus dem Fund: ein Angreifer kennt nur die
    E-Mail-Adresse eines zahlenden Kunden und versucht, sie sich per Signup
    fuer einen EIGENEN, neuen Mandanten zu sichern. Das darf NICHT mehr
    einen zweiten, konkurrierenden Mandanten anlegen."""
    r = _post_stripe_webhook(client, _checkout_completed(
        "evt_hijack_signup", "cus_hijack_signup", "victim-signup@example.ch", "starter",
    ))
    assert r.status_code == 200, r.text
    victim_tenant_id = r.json()["tenant_id"]

    attacker = client.post(
        "/v1/auth/signup",
        json={
            "name": "Attacker Inc",
            "email": "victim-signup@example.ch",
            "password": "attacker-chosen-password",
        },
    )
    assert attacker.status_code == 200, attacker.text
    body = attacker.json()
    # KEIN neuer, konkurrierender Mandant -- das bestehende (Opfer-)Konto
    # wurde stattdessen beansprucht (dokumentiertes Restrisiko ohne
    # E-Mail-Verifikation, siehe README -- aber strukturell KEIN zweiter
    # Mandant fuer dieselbe E-Mail mehr moeglich).
    assert body["tenant_id"] == victim_tenant_id
    assert body["claimed"] is True

    with psycopg.connect(DSN) as c:
        tenant_count = c.execute(
            "SELECT count(*) FROM tenants t JOIN users u ON u.tenant_id = t.id "
            "WHERE u.email = %s",
            ("victim-signup@example.ch",),
        ).fetchone()[0]
    assert tenant_count == 1, "Es darf nur EIN Mandant fuer diese E-Mail existieren"

    # Zweite Verteidigungslinie: ein WEITERER Versuch (jetzt existiert ein
    # Passwort) faellt ganz regulaer auf 409 zurueck -- kein drittes Konto.
    second_attempt = client.post(
        "/v1/auth/signup",
        json={
            "name": "Yet Another Co",
            "email": "victim-signup@example.ch",
            "password": "yet-another-password",
        },
    )
    assert second_attempt.status_code == 409


def test_real_owner_can_claim_passwordless_account_and_then_login(client):
    """Der legitime Gegenfall: der ECHTE Eigentuemer (der Stripe-Kunde selbst,
    ohne je ein Passwort gesetzt zu haben -- z.B. weil seine 30-Tage-
    Autologin-Session abgelaufen ist) nutzt genau denselben Weg, um wieder
    Zugriff zu bekommen: Signup mit der eigenen E-Mail setzt das erste
    Passwort auf dem BESTEHENDEN Konto, und Login funktioniert danach
    normal."""
    r = _post_stripe_webhook(client, _checkout_completed(
        "evt_owner_claim", "cus_owner_claim", "realowner@example.ch", "business",
    ))
    assert r.status_code == 200, r.text
    tenant_id = r.json()["tenant_id"]

    # Frischer Client: simuliert den Kunden OHNE die per Webhook erzeugte
    # Autologin-Session (z.B. abgelaufen/Cookie verloren) -- nur die eigene
    # E-Mail ist ihm bekannt.
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app, base_url="https://testserver") as fresh_client:
        claim = fresh_client.post(
            "/v1/auth/signup",
            json={
                "name": "Real Owner GmbH",
                "email": "realowner@example.ch",
                "password": "the-real-owners-password",
            },
        )
        assert claim.status_code == 200, claim.text
        body = claim.json()
        assert body["tenant_id"] == tenant_id
        assert body["claimed"] is True
        assert body["plan"] == "business"

        # Signup meldet direkt per Session-Cookie an.
        assert fresh_client.get("/v1/usage").status_code == 200
        fresh_client.cookies.clear()

        # Und: ganz normaler Login mit dem gerade gesetzten Passwort.
        login = fresh_client.post(
            "/v1/auth/login",
            json={"email": "realowner@example.ch", "password": "the-real-owners-password"},
        )
        assert login.status_code == 200, login.text
        assert login.json()["tenant_id"] == tenant_id
        assert fresh_client.get("/v1/usage").status_code == 200
