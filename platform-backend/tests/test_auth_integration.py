"""Beweist den Web-Login-Pfad (E-Mail+Passwort, der EINZIGE Auth-Weg der
Plattform) gegen eine echte Postgres-DB: Signup, Login, Session-Cookie-Auth,
Rate-Limiting, und dass der frueher parallel existierende Bearer-Token-Pfad
jetzt wirklich verschwunden ist (kein Fallback, kein Nebeneinander)."""
from __future__ import annotations

import os

import psycopg
import pytest

from app.auth import hash_key
from app.ratelimit import (
    login_limiter_email,
    login_limiter_ip,
    signup_limiter,
    signup_limiter_email,
)

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


@pytest.fixture(autouse=True)
def _reset_limiters():
    limiters = (signup_limiter, signup_limiter_email, login_limiter_ip, login_limiter_email)
    for lim in limiters:
        lim.reset()
    yield
    for lim in limiters:
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
    # Kern der Aufgabe: kein API-Key wird jemals ausgeliefert -- es gibt
    # keinen mehr.
    assert "api_key" not in body
    assert "password" not in body

    # Cookie wurde gesetzt und authentifiziert sofort (gleicher Client, Cookie
    # bleibt in dessen Jar).
    me = client.get("/v1/usage")
    assert me.status_code == 200


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


def test_two_independent_sessions_for_two_accounts_see_only_their_own_tenant(client, client2):
    """Ersetzt den fruaeheren Bearer/Cookie-Paritaetstest (es gibt keinen
    Bearer-Pfad mehr, mit dem man vergleichen koennte): zwei UNABHAENGIGE
    Sessions (zwei Konten, zwei TestClient-Instanzen) sehen jeweils nur ihren
    eigenen Mandanten -- keine Vermischung, kein gemeinsamer Zustand."""
    r1 = _signup(client, email="parity1@example.ch", password="parity-pass-1")
    r2 = _signup(client2, email="parity2@example.ch", password="parity-pass-2")
    assert r1.json()["tenant_id"] != r2.json()["tenant_id"]

    me1 = client.get("/v1/usage")
    me2 = client2.get("/v1/usage")
    assert me1.status_code == 200
    assert me2.status_code == 200


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


def test_signup_email_rate_limited_across_repeated_attempts(client, monkeypatch):
    """Security-Review Punkt C: zusaetzlich zum IP-Limit bremst ein
    E-Mail-spezifisches Limit Masse-Enumeration/-Angriffe GEGEN DIESELBE
    Ziel-E-Mail (z.B. wiederholte Versuche, ein bestimmtes Konto zu
    beanspruchen oder dessen Existenz per 409-vs-200 zu erraten) -- auch
    wenn das IP-Limit selbst grosszuegig genug waere."""
    monkeypatch.setattr(signup_limiter, "max_calls", 1000)  # IP-Limit soll hier nicht greifen
    monkeypatch.setattr(signup_limiter_email, "max_calls", 2)

    # Erster Versuch: echter Signup, legt das Konto an.
    first = _signup(client, email="emailratelimited@example.ch", password="first-password")
    assert first.status_code == 200
    client.post("/v1/auth/logout")

    # Zweiter Versuch (selbe E-Mail, jetzt schon mit Passwort) -> regulaeres
    # 409, zaehlt aber weiterhin gegen das E-Mail-Limit.
    second = _signup(client, email="emailratelimited@example.ch", password="second-password")
    assert second.status_code == 409

    # Dritter Versuch: das E-Mail-Limit (max_calls=2) ist jetzt ausgeschoepft
    # -> 429, VOR jeder weiteren Pruefung.
    third = _signup(client, email="emailratelimited@example.ch", password="third-password")
    assert third.status_code == 429
    assert "Retry-After" in third.headers


def test_bearer_token_path_is_completely_gone(client, prov):
    """Regression fuer den Kern dieser Aufgabe: der Bearer-API-Key-Pfad ist
    NICHT nur optional/zusaetzlich -- er existiert im Code ueberhaupt nicht
    mehr. Selbst ein wohlgeformt aussehender, frei erfundener Bearer-Token
    wird ignoriert (require_principal liest den Authorization-Header gar
    nicht mehr), nicht etwa "auch akzeptiert"."""
    prov("free")  # echte, gueltige Session -- beweist, dass NUR sie zaehlt
    assert client.get("/v1/usage").status_code == 200

    client.cookies.clear()
    r = client.get(
        "/v1/usage", headers={"Authorization": "Bearer pk_" + "a" * 40}
    )
    assert r.status_code == 401
