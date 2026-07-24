"""E2E-Integrationstest der Agenten-Ebene gegen eine echte Postgres-DB:
Tarif-Limit (max_agents) + Modell-Gating + RLS-Isolation zwischen Mandanten.

Laeuft nur mit gesetzter PLATFORM_TEST_DATABASE_URL (privilegierte Verbindung).
"""
from __future__ import annotations

import os
import urllib.parse as up

import pytest

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


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

    from app.main import app

    with TestClient(app) as c:
        yield c
    close_pool()


def _provision(client, plan="free"):
    r = client.post(
        "/admin/provision",
        headers={"X-Admin-Token": "test-admin"},
        json={"tenant_name": "T", "owner_email": "t@example.ch", "plan_code": plan},
    )
    assert r.status_code == 200, r.text
    return r.json()["api_key"]


def test_max_agents_limit_enforced(client):
    key = _provision(client, "free")  # free: max_agents=1, Modelle: ollama/llama3.2
    h = {"Authorization": "Bearer " + key}

    r1 = client.post("/v1/agents", headers=h, json={"name": "A1", "model": "ollama/llama3.2"})
    assert r1.status_code == 201, r1.text

    # Zweiter Agent -> Limit erreicht.
    r2 = client.post("/v1/agents", headers=h, json={"name": "A2", "model": "ollama/llama3.2"})
    assert r2.status_code == 403
    assert "Limit" in r2.json()["detail"]

    lst = client.get("/v1/agents", headers=h).json()
    assert lst["count"] == 1 and lst["max_agents"] == 1


def test_model_gating_on_agent_create(client):
    key = _provision(client, "free")
    h = {"Authorization": "Bearer " + key}
    # Nicht im Free-Tarif freigeschaltet.
    r = client.post("/v1/agents", headers=h, json={"name": "X", "model": "anthropic/claude-opus-4-8"})
    assert r.status_code == 403
    # Unbekanntes Modell.
    r2 = client.post("/v1/agents", headers=h, json={"name": "Y", "model": "fantasie/z"})
    assert r2.status_code == 403


def test_agents_isolated_between_tenants(client):
    key_a = _provision(client, "free")
    key_b = _provision(client, "free")
    ha = {"Authorization": "Bearer " + key_a}
    hb = {"Authorization": "Bearer " + key_b}

    created = client.post("/v1/agents", headers=ha, json={"name": "GeheimA", "model": "ollama/llama3.2"})
    assert created.status_code == 201
    agent_id = created.json()["id"]

    # B sieht A's Agenten nicht (RLS).
    assert client.get("/v1/agents", headers=hb).json()["count"] == 0
    # B kann A's Agenten nicht abrufen.
    assert client.get(f"/v1/agents/{agent_id}", headers=hb).status_code == 404
    # A schon.
    assert client.get(f"/v1/agents/{agent_id}", headers=ha).status_code == 200
