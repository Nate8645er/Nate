"""Beweist den neuen Web-Login-Pfad (E-Mail+Passwort statt rohem API-Key)
gegen eine echte Postgres-DB: Signup, Login, Session-Cookie-Auth,
Rate-Limiting, und dass der bestehende Bearer-Token-Pfad unveraendert
weiterfunktioniert (Regression)."""
from __future__ import annotations

import os

import psycopg
import pytest

from app.auth import generate_key, hash_key
from app.ratelimit import login_limiter_email, login_limiter_ip, signup_limiter

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


@pytest.fixture(autouse=True)
def _reset_limiters():
    for lim in (signup_limiter, login_limiter_ip, login_limiter_email):
        lim.reset()
    yield
    for lim in (signup_limiter, login_limiter_ip, login_limiter_email):
        lim.reset()


def _signup(client, name="Acme", email="owner@example.ch", password="hunter2ok"):
    return client.post(
        "/v1/auth/signup", json={"name": name, "email": email, "password": password}
    )


def test_signup_creates_tenant_user_and_working_session(client):
    r = _signup(client)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["plan"] == "free"
    assert "tenant_id" in body
    # Kern der Aufgabe: der Roh-API-Key wird fuer den Web-Pfad NIE ausgeliefert.
    assert "api_key" not in body
    assert "password" not in body

    # Cookie wurde gesetzt und authentifiziert sofort (gleicher Client, Cookie
    # bleibt in dessen Jar).
    me = client.get("/v1/usage")
    assert me.status_code == 200, me.text


def test_login_after_signup_with_same_credentials(client):
    r = _signup(client, email="login1@example.ch", password="correct-horse")
    assert r.status_code == 200
    client.post("/v1/auth/logout")

    # Ohne Session darf der geschuetzte Endpunkt nicht mehr funktionieren.
    assert client.get("/v1/usage").status_code == 401

    login = client.post(
        "/v1/auth/login", json={"email": "login1@example.ch", "password": "correct-horse"}
    )
    assert login.status_code == 200, login.text
    assert login.json()["tenant_id"] == r.json()["tenant_id"]
    assert client.get("/v1/usage").status_code == 200


def test_wrong_password_and_unknown_email_are_indistinguishable(client):
    _signup(client, email="login2@example.ch", password="correct-horse")

    wrong = client.post(
        "/v1/auth/login", json={"email": "login2@example.ch", "password": "totally-wrong"}
    )
    unknown = client.post(
        "/v1/auth/login", json={"email": "never-registered@example.ch", "password": "whatever1"}
    )
    assert wrong.status_code == 401
    assert unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]


def test_duplicate_signup_email_is_rejected_without_orphaned_tenant(client):
    first = _signup(client, email="dup@example.ch", password="first-password")
    assert first.status_code == 200

    second = _signup(client, name="AnotherCo", email="dup@example.ch", password="second-password")
    assert second.status_code == 409

    # Der ERSTE Mandant bleibt unversehrt nutzbar (kein Teil-Rollback-Schaden).
    login = client.post(
        "/v1/auth/login", json={"email": "dup@example.ch", "password": "first-password"}
    )
    assert login.status_code == 200


def test_signup_rejects_short_password(client):
    r = client.post(
        "/v1/auth/signup",
        json={"name": "X", "email": "shortpw@example.ch", "password": "short"},
    )
    assert r.status_code == 422


def test_session_cookie_yields_same_principal_as_bearer_token(client):
    r = _signup(client, email="parity@example.ch", password="parity-pass")
    tenant_id = r.json()["tenant_id"]
    via_cookie = client.get("/v1/usage")
    assert via_cookie.status_code == 200

    # Fuer denselben Mandanten direkt (ausserhalb der App) einen zweiten
    # API-Key anlegen -- beweist: Bearer-Pfad und Cookie-Pfad liefern fuer
    # denselben Mandanten denselben Principal (RLS-konform identische Sicht).
    clear_key, key_hash = generate_key()
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute(
            "INSERT INTO api_keys (tenant_id, key_hash, label) VALUES (%s, %s, 'test-parity')",
            (tenant_id, key_hash),
        )

    client.cookies.clear()
    via_bearer = client.get("/v1/usage", headers={"Authorization": "Bearer " + clear_key})
    assert via_bearer.status_code == 200
    assert via_bearer.json() == via_cookie.json()


def test_unknown_session_cookie_is_401(client):
    client.cookies.set("session", "does-not-exist-at-all")
    r = client.get("/v1/usage")
    assert r.status_code == 401
    client.cookies.clear()


def test_expired_session_cookie_is_401(client):
    r = _signup(client, email="expiring@example.ch", password="expiring-pass")
    tenant_id = r.json()["tenant_id"]
    token = client.cookies.get("session")
    assert token

    # Serverseitig auf abgelaufen zuruecksetzen -- der Klartext-Token im
    # Cookie bleibt gleich, nur sein Hash in der DB zaehlt jetzt als abgelaufen.
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute(
            "UPDATE sessions SET expires_at = now() - interval '1 hour' WHERE token_hash = %s",
            (hash_key(token),),
        )
    r2 = client.get("/v1/usage")
    assert r2.status_code == 401
    assert tenant_id  # nur zur Klarheit im Testverlauf verwendet


def test_login_rate_limited_after_repeated_failures(client, monkeypatch):
    _signup(client, email="bruteforce@example.ch", password="the-real-password")
    client.cookies.clear()
    monkeypatch.setattr(login_limiter_email, "max_calls", 2)

    for _ in range(2):
        r = client.post(
            "/v1/auth/login", json={"email": "bruteforce@example.ch", "password": "wrong"}
        )
        assert r.status_code == 401

    r3 = client.post(
        "/v1/auth/login", json={"email": "bruteforce@example.ch", "password": "wrong"}
    )
    assert r3.status_code == 429
    assert "Retry-After" in r3.headers


def test_signup_rate_limited_after_repeated_calls(client, monkeypatch):
    monkeypatch.setattr(signup_limiter, "max_calls", 2)
    for i in range(2):
        r = _signup(client, email=f"ratelimited{i}@example.ch", password="whatever-pass")
        assert r.status_code == 200
        client.post("/v1/auth/logout")

    r3 = _signup(client, email="ratelimited-blocked@example.ch", password="whatever-pass")
    assert r3.status_code == 429


def test_existing_bearer_token_login_path_still_works(client, prov):
    """Regression: der unveraenderte API-Key-Pfad (Master-Prompt-Fundament)
    darf durch die neuen Auth-Routen nicht angetastet worden sein."""
    key = prov("free")
    r = client.get("/v1/usage", headers={"Authorization": "Bearer " + key})
    assert r.status_code == 200
    # Ohne jede Authentifizierung weiterhin klar abgelehnt.
    client.cookies.clear()
    assert client.get("/v1/usage").status_code == 401
