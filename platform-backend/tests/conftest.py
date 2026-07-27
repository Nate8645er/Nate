"""Gemeinsame Test-Fixtures. Der `client` gegen eine echte Postgres-DB wird
von den Integrationstests genutzt (nur wenn PLATFORM_TEST_DATABASE_URL gesetzt
ist; sonst skippen die jeweiligen Module selbst)."""
from __future__ import annotations

import itertools
import os
import urllib.parse as up

import pytest

# Dummy-Verbindungsdaten, damit app.config beim Import nicht scheitert. Reine
# Unit-Tests fassen die DB nicht an (der Pool oeffnet lazy); die Integrations-
# Fixture unten setzt die echten Werte direkt auf `settings`.
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@127.0.0.1:1/db")
os.environ.setdefault("MIGRATE_DATABASE_URL", "postgresql://u:p@127.0.0.1:1/db")

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")

# Jeder prov()/prov2()-Aufruf braucht eine GLOBAL (innerhalb des laufenden
# Tests) eindeutige E-Mail, weil provision_tenant() jetzt immer ein Passwort
# setzt und damit in `user_directory` eintraegt (PRIMARY KEY auf
# email_lower) -- anders als beim fruaeheren API-Key-Pfad, der nie ueber
# diese Tabelle lief. Ein modulweiter Zaehler reicht: `tenants` (und per
# CASCADE `user_directory`) wird von der `client`-Fixture vor JEDEM Test neu
# geleert, Kollisionen ueber Testgrenzen hinweg sind also ausgeschlossen.
_PROV_COUNTER = itertools.count()


@pytest.fixture(autouse=True)
def _reset_rate_limiters_between_tests():
    """Verhindert Test-Verkopplung ueber die (bewusst prozessweiten, In-
    Memory-) Rate-Limiter aus app/ratelimit.py: `prov()`/`prov2()` melden
    sich jetzt per /v1/auth/login an (statt nur /admin/provision aufzurufen
    wie beim fruaeheren API-Key-Pfad) und zaehlen damit gegen
    login_limiter_ip/login_limiter_email mit. Ohne Reset wuerde sich das
    ueber viele Testdateien/-faelle hinweg aufsummieren und irgendwann
    faelschlich 429 ausloesen -- unabhaengig vom eigentlichen Testinhalt.
    Tests, die das Rate-Limiting SELBST pruefen (test_auth_integration.py,
    test_ratelimit_integration.py), haben zusaetzlich eigene lokale
    Reset-Fixtures; ein doppelter reset() ist no-op/harmlos."""
    from app.ratelimit import (
        chat_limiter,
        checkout_claim_limiter,
        login_limiter_email,
        login_limiter_ip,
        signup_limiter,
        signup_limiter_email,
    )

    limiters = (
        chat_limiter,
        signup_limiter,
        signup_limiter_email,
        login_limiter_ip,
        login_limiter_email,
        checkout_claim_limiter,
    )
    for lim in limiters:
        lim.reset()
    yield
    for lim in limiters:
        lim.reset()


@pytest.fixture()
def client():
    import psycopg
    from fastapi.testclient import TestClient

    from app.config import settings
    from app.db import close_pool, migrate

    close_pool()
    settings.migrate_database_url = DSN
    migrate()

    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute("ALTER ROLE app_rw LOGIN PASSWORD 'app_rw_test'")
        # Sauberer Zustand pro Test: Mandanten (CASCADE raeumt users/sessions/
        # user_directory/conversations/messages/usage_events/agents/
        # billing_events/checkout_handoffs mit ab) und die Idempotenz-Tabelle.
        # `plans` bleibt (kommt aus der Migration).
        conn.execute("TRUNCATE tenants, processed_webhooks CASCADE")

    p = up.urlparse(DSN)
    settings.database_url = (
        f"postgresql://app_rw:app_rw_test@{p.hostname}:{p.port or 5432}{p.path}"
    )
    close_pool()
    os.environ["ADMIN_TOKEN"] = "test-admin"
    os.environ["SHOPIFY_WEBHOOK_SECRET"] = "test-shop-secret"
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_integration"

    from app.main import app

    # base_url="https://..." statt des Standards "http://testserver": die
    # Session-Cookies aus app/auth.py setzen bewusst das Secure-Flag (siehe
    # dortiger Kommentar). httpx' Cookie-Jar haengt Secure-Cookies NUR an
    # Requests mit https-Schema an -- mit dem http-Standard wuerde jeder
    # Test, der nach dem Login eine authentifizierte Folgeanfrage erwartet,
    # das Cookie stillschweigend verlieren (kein echter TLS-Handshake noetig,
    # es ist nur die Schema-Pruefung der Cookie-Jar-Logik).
    with TestClient(app, base_url="https://testserver") as c:
        yield c
    close_pool()


@pytest.fixture()
def client2(client):
    """Zweite, unabhaengige TestClient-Instanz (eigenes Cookie-Jar) gegen
    dieselbe App/DB -- fuer Tests, die zwei Mandanten GLEICHZEITIG
    authentifiziert brauchen (z.B. RLS-Isolation zwischen zwei Mandanten).
    Ein einzelner `client` haelt immer nur EINE Sitzung gleichzeitig
    (TestClient/httpx verwalten Cookies pro Instanz) -- ein zweiter prov()-
    Aufruf auf DEMSELBEN Client wuerde dessen Session einfach ueberschreiben,
    nicht eine zweite parallel gueltige Sitzung erzeugen.

    Haengt bewusst von `client` ab (auch wenn ungenutzt): erzwingt, dass
    Migration/Truncate/Env-Setup bereits gelaufen sind, bevor eine zweite
    Instanz gegen dieselbe DB oeffnet."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app, base_url="https://testserver") as c:
        yield c


def _provision_and_login(target_client, plan: str) -> str:
    """Provisioniert einen Mandanten im gegebenen Tarif ueber /admin/provision
    (jetzt mit Pflicht-Passwort statt eines API-Keys) und meldet
    `target_client` sofort per /v1/auth/login mit diesem Passwort an --
    TestClient haelt das Session-Cookie danach automatisch fuer alle
    Folge-Requests auf DERSELBEN Instanz (siehe Docstring der `client`-
    Fixture). Gibt die tenant_id zurueck (frueher: der Klartext-API-Key)."""
    n = next(_PROV_COUNTER)
    email = f"prov{n}@example.ch"
    password = "prov-test-password-1"  # noqa: S105 -- Test-Fixture, kein echtes Geheimnis
    r = target_client.post(
        "/admin/provision",
        headers={"X-Admin-Token": "test-admin"},
        json={"tenant_name": "T", "owner_email": email, "plan_code": plan, "password": password},
    )
    assert r.status_code == 200, r.text
    tenant_id = r.json()["tenant_id"]

    login = target_client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return tenant_id


@pytest.fixture()
def prov(client):
    """Liefert prov(plan) -> tenant_id (frueher: -> api_key). Meldet `client`
    per Session-Cookie an -- Folge-Requests auf demselben `client` sind
    automatisch authentifiziert, kein Header noetig."""
    def _p(plan="free"):
        return _provision_and_login(client, plan)
    return _p


@pytest.fixture()
def prov2(client2):
    """Wie `prov`, aber fuer die zweite, unabhaengige `client2`-Instanz --
    fuer Tests, die zwei gleichzeitig gueltige Sitzungen brauchen."""
    def _p(plan="free"):
        return _provision_and_login(client2, plan)
    return _p
