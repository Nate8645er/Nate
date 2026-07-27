"""Tests der Metriken (Phase 7, Monitoring). Unit-Teil ohne DB, E2E gegen
den echten TestClient (beweist: /metrics zaehlt echte Requests mit)."""
from __future__ import annotations

from app.main import app


def test_metrics_endpoint_exposes_prometheus_format():
    from fastapi.testclient import TestClient

    client = TestClient(app)
    # Ein paar Requests erzeugen, damit /metrics nicht leer ist.
    client.get("/health")
    client.get("/health")
    client.get("/v1/models")  # 401 ohne Auth — zaehlt trotzdem als Request

    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]
    body = r.text

    assert 'http_requests_total{method="GET",route="/health",status="200"}' in body
    # Route-Templates statt dynamischer Pfade -> /v1/models bleibt genau so,
    # keine IDs im Label.
    assert 'route="/v1/models"' in body
    assert "http_request_duration_seconds" in body


def test_path_params_use_route_template_not_raw_id():
    """Verhindert Kardinalitaets-Explosion: verschiedene UUIDs im Pfad muessen
    unter demselben Label ({agent_id}) gezaehlt werden, nicht als eigene
    Zeitreihe pro ID."""
    from fastapi.testclient import TestClient

    # Kein Session-Cookie vorhanden -> require_principal wirft 401 SOFORT,
    # ohne DB-Zugriff (der Authorization-Header wird gar nicht mehr gelesen,
    # es gibt keinen Bearer-Pfad mehr). Das Routing (und damit
    # scope["route"]) ist zu diesem Zeitpunkt trotzdem schon aufgeloest —
    # passendes Muster fuer diesen DB-freien Testlauf.
    client = TestClient(app)
    client.get("/v1/agents/11111111-1111-1111-1111-111111111111", headers={"Authorization": "Token x"})
    client.get("/v1/agents/22222222-2222-2222-2222-222222222222", headers={"Authorization": "Token x"})

    body = client.get("/metrics").text
    assert 'route="/v1/agents/{agent_id}"' in body
    assert "11111111" not in body
    assert "22222222" not in body


def test_metrics_route_itself_not_recursively_broken():
    from fastapi.testclient import TestClient

    client = TestClient(app)
    r1 = client.get("/metrics")
    assert r1.status_code == 200
    # Zweiter Aufruf funktioniert weiterhin (Counter akkumulieren, kein Crash).
    r2 = client.get("/metrics")
    assert r2.status_code == 200
