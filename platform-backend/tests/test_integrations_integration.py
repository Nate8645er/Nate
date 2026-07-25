"""E2E-Integrationstest der Integrations-Ebene gegen eine echte Postgres-DB:
Provider-Validierung + Tarif-Limit (max_integrations) + RLS-Isolation
zwischen Mandanten.

Laeuft nur mit gesetzter PLATFORM_TEST_DATABASE_URL (privilegierte Verbindung).
"""
from __future__ import annotations

import os

import pytest

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


def test_unknown_provider_rejected(client, prov):
    key = prov("starter")
    h = {"Authorization": "Bearer " + key}
    r = client.post("/v1/integrations", headers=h, json={"provider": "discord"})
    assert r.status_code == 400
    assert "discord" in r.json()["detail"]


def test_max_integrations_limit_zero_on_free(client, prov):
    # free: max_integrations=0 -> jeder Versuch wird sofort abgelehnt.
    key = prov("free")
    h = {"Authorization": "Bearer " + key}
    r = client.post("/v1/integrations", headers=h, json={"provider": "slack"})
    assert r.status_code == 403
    assert "Limit" in r.json()["detail"]

    lst = client.get("/v1/integrations", headers=h).json()
    assert lst["count"] == 0


def test_max_integrations_limit_enforced_on_starter(client, prov):
    # starter: max_integrations=1 -> erste Integration klappt, zweite nicht.
    key = prov("starter")
    h = {"Authorization": "Bearer " + key}

    r1 = client.post("/v1/integrations", headers=h, json={"provider": "slack"})
    assert r1.status_code == 201, r1.text
    body = r1.json()
    assert body["provider"] == "slack"
    # Kein echter OAuth-Flow -> status bleibt immer 'disconnected'.
    assert body["status"] == "disconnected"

    r2 = client.post("/v1/integrations", headers=h, json={"provider": "notion"})
    assert r2.status_code == 403
    assert "Limit" in r2.json()["detail"]

    lst = client.get("/v1/integrations", headers=h).json()
    assert lst["count"] == 1


def test_integrations_isolated_between_tenants(client, prov):
    key_a = prov("starter")
    key_b = prov("starter")
    ha = {"Authorization": "Bearer " + key_a}
    hb = {"Authorization": "Bearer " + key_b}

    created = client.post("/v1/integrations", headers=ha, json={"provider": "google"})
    assert created.status_code == 201
    integration_id = created.json()["id"]

    # B sieht A's Integrationen nicht (RLS).
    assert client.get("/v1/integrations", headers=hb).json()["count"] == 0
    # B kann A's Integration nicht loeschen.
    assert client.delete(f"/v1/integrations/{integration_id}", headers=hb).status_code == 404
    # A schon.
    assert client.delete(f"/v1/integrations/{integration_id}", headers=ha).status_code == 204


def test_delete_own_integration_then_404_for_foreign(client, prov):
    key_a = prov("starter")
    key_b = prov("starter")
    ha = {"Authorization": "Bearer " + key_a}
    hb = {"Authorization": "Bearer " + key_b}

    created = client.post("/v1/integrations", headers=ha, json={"provider": "notion"})
    integration_id = created.json()["id"]

    # Eigene Integration loeschen klappt.
    assert client.delete(f"/v1/integrations/{integration_id}", headers=ha).status_code == 204
    # Nochmal loeschen -> schon weg -> 404.
    assert client.delete(f"/v1/integrations/{integration_id}", headers=ha).status_code == 404
    # Fremde (nie existierte fuer B) -> 404.
    assert client.delete(f"/v1/integrations/{integration_id}", headers=hb).status_code == 404
