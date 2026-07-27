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
    prov("free")  # free: max_agents=1, Modelle: ollama/llama3.2

    r1 = client.post("/v1/agents", json={"name": "A1", "model": "ollama/llama3.2"})
    assert r1.status_code == 201, r1.text

    # Zweiter Agent -> Limit erreicht.
    r2 = client.post("/v1/agents", json={"name": "A2", "model": "ollama/llama3.2"})
    assert r2.status_code == 403
    assert "Limit" in r2.json()["detail"]

    lst = client.get("/v1/agents").json()
    assert lst["count"] == 1 and lst["max_agents"] == 1


def test_agent_chat_rejects_image_for_non_vision_model(client, prov):
    """Regression: AgentChatRequest.messages nutzt dieselbe multimodale
    ChatMessage-Klasse wie /v1/chat -- ein Bild-Anhang an einen Agenten mit
    einem Nicht-Vision-Modell muss dieselbe 400-Ablehnung bekommen wie im
    normalen Chat-Pfad, statt unvalidiert (kein Groessen-/Signaturcheck) an
    das Gateway durchgereicht zu werden."""
    prov("free")  # free: ollama/llama3.2 (vision=False)
    agent = client.post("/v1/agents", json={"name": "A", "model": "ollama/llama3.2"})
    assert agent.status_code == 201, agent.text
    agent_id = agent.json()["id"]

    tiny_png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
        "+A8AAQUBAScY42YAAAAASUVORK5CYII="
    )
    r = client.post(
        f"/v1/agents/{agent_id}/chat",
        json={"messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Was ist auf dem Bild?"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{tiny_png_b64}"}},
            ],
        }]},
    )
    assert r.status_code == 400, r.text
    assert "unterstuetzt keine Bild-Eingabe" in r.json()["detail"]


def test_model_gating_on_agent_create(client, prov):
    prov("free")
    # Nicht im Free-Tarif freigeschaltet.
    r = client.post("/v1/agents", json={"name": "X", "model": "anthropic/claude-opus-4-8"})
    assert r.status_code == 403
    # Unbekanntes Modell.
    r2 = client.post("/v1/agents", json={"name": "Y", "model": "fantasie/z"})
    assert r2.status_code == 403


def test_agents_isolated_between_tenants(client, client2, prov, prov2):
    prov("free")
    prov2("free")

    created = client.post("/v1/agents", json={"name": "GeheimA", "model": "ollama/llama3.2"})
    assert created.status_code == 201
    agent_id = created.json()["id"]

    # B (client2, eigene Sitzung) sieht A's Agenten nicht (RLS).
    assert client2.get("/v1/agents").json()["count"] == 0
    # B kann A's Agenten nicht abrufen.
    assert client2.get(f"/v1/agents/{agent_id}").status_code == 404
    # A schon.
    assert client.get(f"/v1/agents/{agent_id}").status_code == 200


def test_run_unknown_agent_404(client, prov):
    prov("free")
    r = client.post(
        "/v1/agents/00000000-0000-0000-0000-000000000000/chat",
        json={"messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code == 404


def test_run_agent_reaches_gateway(client, prov):
    # Kein Gateway erreichbar -> die Bahn laeuft bis zum Gateway und liefert 502
    # (beweist: Agent geladen, Modell akzeptiert, Limit ok, Weiterleitung).
    prov("free")
    created = client.post("/v1/agents", json={"name": "Run", "model": "ollama/llama3.2"})
    agent_id = created.json()["id"]
    r = client.post(
        f"/v1/agents/{agent_id}/chat",
        json={"messages": [{"role": "user", "content": "hallo"}]},
    )
    assert r.status_code == 502
