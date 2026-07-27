"""Gemeinsame Test-Fixtures. Der `client` gegen eine echte Postgres-DB wird
von den Integrationstests genutzt (nur wenn PLATFORM_TEST_DATABASE_URL gesetzt
ist; sonst skippen die jeweiligen Module selbst)."""
from __future__ import annotations

import os
import urllib.parse as up

import pytest

# Dummy-Verbindungsdaten, damit app.config beim Import nicht scheitert. Reine
# Unit-Tests fassen die DB nicht an (der Pool oeffnet lazy); die Integrations-
# Fixture unten setzt die echten Werte direkt auf `settings`.
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@127.0.0.1:1/db")
os.environ.setdefault("MIGRATE_DATABASE_URL", "postgresql://u:p@127.0.0.1:1/db")

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")


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
        # Sauberer Zustand pro Test: Mandanten (CASCADE raeumt users/api_keys/
        # conversations/messages/usage_events/agents/billing_events mit ab) und
        # die Idempotenz-Tabelle. `plans` bleibt (kommt aus der Migration).
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
    # Session-Cookies aus app/routes/auth.py setzen bewusst das Secure-Flag
    # (siehe dortiger Kommentar). httpx' Cookie-Jar haengt Secure-Cookies NUR
    # an Requests mit https-Schema an -- mit dem http-Standard wuerde jeder
    # Test, der nach dem Login eine authentifizierte Folgeanfrage erwartet,
    # das Cookie stillschweigend verlieren (kein echter TLS-Handshake noetig,
    # es ist nur die Schema-Pruefung der Cookie-Jar-Logik).
    with TestClient(app, base_url="https://testserver") as c:
        yield c
    close_pool()


@pytest.fixture()
def prov(client):
    """Liefert einen Helfer prov(plan) -> api_key (provisioniert einen Mandanten)."""
    def _p(plan="free"):
        r = client.post(
            "/admin/provision",
            headers={"X-Admin-Token": "test-admin"},
            json={"tenant_name": "T", "owner_email": "t@example.ch", "plan_code": plan},
        )
        assert r.status_code == 200, r.text
        return r.json()["api_key"]

    return _p
