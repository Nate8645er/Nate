"""Beweist den echten Composio-Anschluss in /v1/integrations gegen eine
echte Postgres-DB, mit einem gefaelschten Composio-Toolset (kein echter
Composio-Account in dieser Umgebung vorhanden) -- prueft aber den
tatsaechlichen Code-Pfad in app/routes/integrations.py, nicht nur die
Attrappe selbst."""
from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


class _FakeToolsetOK:
    def initiate_connection(self, app, redirect_url=None):
        return SimpleNamespace(
            connectedAccountId="fake-account-123",
            redirectUrl="https://composio.example/connect/fake-account-123",
        )

    def get_connected_account(self, account_id):
        assert account_id == "fake-account-123"
        return SimpleNamespace(status="ACTIVE")


class _FakeToolsetFails:
    def initiate_connection(self, app, redirect_url=None):
        raise RuntimeError("Composio ist down (simuliert)")


def test_create_without_composio_configured_unchanged(client, prov, monkeypatch):
    """Ohne COMPOSIO_API_KEY: exakt das bisherige Geruest-Verhalten."""
    monkeypatch.setattr("app.routes.integrations.build_toolset", lambda: None)
    key = prov("starter")
    h = {"Authorization": "Bearer " + key}
    r = client.post("/v1/integrations", headers=h, json={"provider": "slack"})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "disconnected"
    assert body["connect_url"] is None
    assert "composio_connected_account_id" not in body["config"]


def test_create_with_composio_returns_connect_url(client, prov, monkeypatch):
    monkeypatch.setattr("app.routes.integrations.build_toolset", lambda: _FakeToolsetOK())
    key = prov("starter")
    h = {"Authorization": "Bearer " + key}
    r = client.post("/v1/integrations", headers=h, json={"provider": "slack"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["connect_url"] == "https://composio.example/connect/fake-account-123"
    assert body["config"]["composio_connected_account_id"] == "fake-account-123"
    # Ohne Bestaetigung durch refresh bleibt der Status disconnected.
    assert body["status"] == "disconnected"


def test_create_with_composio_failure_creates_no_row(client, prov, monkeypatch):
    monkeypatch.setattr("app.routes.integrations.build_toolset", lambda: _FakeToolsetFails())
    key = prov("starter")
    h = {"Authorization": "Bearer " + key}
    r = client.post("/v1/integrations", headers=h, json={"provider": "slack"})
    assert r.status_code == 502

    # Kein Datensatz angelegt -- das Tarif-Kontingent bleibt unangetastet.
    monkeypatch.setattr("app.routes.integrations.build_toolset", lambda: None)
    lst = client.get("/v1/integrations", headers=h).json()
    assert lst["count"] == 0


def test_refresh_without_stored_connection_is_400(client, prov, monkeypatch):
    monkeypatch.setattr("app.routes.integrations.build_toolset", lambda: None)
    key = prov("starter")
    h = {"Authorization": "Bearer " + key}
    created = client.post("/v1/integrations", headers=h, json={"provider": "notion"})
    integration_id = created.json()["id"]

    r = client.post(f"/v1/integrations/{integration_id}/refresh", headers=h)
    assert r.status_code == 400


def test_refresh_marks_connected_when_composio_reports_active(client, prov, monkeypatch):
    monkeypatch.setattr("app.routes.integrations.build_toolset", lambda: _FakeToolsetOK())
    key = prov("starter")
    h = {"Authorization": "Bearer " + key}
    created = client.post("/v1/integrations", headers=h, json={"provider": "slack"})
    integration_id = created.json()["id"]
    assert created.json()["status"] == "disconnected"

    r = client.post(f"/v1/integrations/{integration_id}/refresh", headers=h)
    assert r.status_code == 200
    assert r.json()["status"] == "connected"

    # Bleibt auch beim erneuten Abrufen so.
    lst = client.get("/v1/integrations", headers=h).json()
    assert lst["integrations"][0]["status"] == "connected"
