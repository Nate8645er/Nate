"""E2E-Integrationstest der Agenten-Ebene gegen eine echte Postgres-DB:
Tarif-Limit (max_agents) + Modell-Gating + RLS-Isolation zwischen Mandanten.

Laeuft nur mit gesetzter PLATFORM_TEST_DATABASE_URL (privilegierte Verbindung).
"""
from __future__ import annotations

import os

import pytest

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


def test_max_agents_limit_enforced(client, prov):
    key = prov("free")  # free: max_agents=1, Modelle: ollama/llama3.2
    h = {"Authorization": "Bearer " + key}

    r1 = client.post("/v1/agents", headers=h, json={"name": "A1", "model": "ollama/llama3.2"})
    assert r1.status_code == 201, r1.text

    # Zweiter Agent -> Limit erreicht.
    r2 = client.post("/v1/agents", headers=h, json={"name": "A2", "model": "ollama/llama3.2"})
    assert r2.status_code == 403
    assert "Limit" in r2.json()["detail"]

    lst = client.get("/v1/agents", headers=h).json()
    assert lst["count"] == 1 and lst["max_agents"] == 1


def test_model_gating_on_agent_create(client, prov):
    key = prov("free")
    h = {"Authorization": "Bearer " + key}
    # Nicht im Free-Tarif freigeschaltet.
    r = client.post("/v1/agents", headers=h, json={"name": "X", "model": "anthropic/claude-opus-4-8"})
    assert r.status_code == 403
    # Unbekanntes Modell.
    r2 = client.post("/v1/agents", headers=h, json={"name": "Y", "model": "fantasie/z"})
    assert r2.status_code == 403


def test_agents_isolated_between_tenants(client, prov):
    key_a = prov("free")
    key_b = prov("free")
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


def test_run_unknown_agent_404(client, prov):
    key = prov("free")
    h = {"Authorization": "Bearer " + key}
    r = client.post(
        "/v1/agents/00000000-0000-0000-0000-000000000000/chat",
        headers=h,
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code == 404


def test_run_agent_reaches_gateway(client, prov):
    # Kein Gateway erreichbar -> die Bahn laeuft bis zum Gateway und liefert 502
    # (beweist: Agent geladen, Modell akzeptiert, Limit ok, Weiterleitung).
    key = prov("free")
    h = {"Authorization": "Bearer " + key}
    created = client.post("/v1/agents", headers=h, json={"name": "Run", "model": "ollama/llama3.2"})
    agent_id = created.json()["id"]
    r = client.post(
        f"/v1/agents/{agent_id}/chat",
        headers=h,
        json={"messages": [{"role": "user", "content": "hallo"}]},
    )
    assert r.status_code == 502
