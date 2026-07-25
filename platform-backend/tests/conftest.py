"""Gemeinsame Test-Fixtures. Der `client` gegen eine echte Postgres-DB wird
von den Integrationstests genutzt (nur wenn PLATFORM_TEST_DATABASE_URL gesetzt
ist; sonst skippen die jeweiligen Module selbst)."""
from __future__ import annotations

import os
import urllib.parse as up

import pytest

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

    p = up.urlparse(DSN)
    settings.database_url = (
        f"postgresql://app_rw:app_rw_test@{p.hostname}:{p.port or 5432}{p.path}"
    )
    close_pool()
    os.environ["ADMIN_TOKEN"] = "test-admin"
    os.environ["SHOPIFY_WEBHOOK_SECRET"] = "test-shop-secret"

    from app.main import app

    with TestClient(app) as c:
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
