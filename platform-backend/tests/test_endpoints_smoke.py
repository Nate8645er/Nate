"""Smoke-Tests der Endpunkt-Verdrahtung: Routing + Auth-Gate + statisches UI.
Ohne DB — die geschuetzten Routen antworten 401, bevor sie die DB beruehren."""
import os

# Dummy-Env, damit config importierbar ist (Pool wird lazy erst bei DB-Zugriff
# geoeffnet; diese Tests treffen keinen DB-Pfad).
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@127.0.0.1:1/db")
os.environ.setdefault("MIGRATE_DATABASE_URL", "postgresql://u:p@127.0.0.1:1/db")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_protected_routes_require_auth():
    assert client.get("/v1/models").status_code == 401
    assert client.get("/v1/usage").status_code == 401
    assert client.get("/v1/conversations").status_code == 401
    assert client.post("/v1/chat", json={"model": "x", "messages": [{"role": "user", "content": "hi"}]}).status_code == 401


def test_bad_bearer_is_rejected_shape():
    # Falsches Schema -> 401 (kein DB-Zugriff noetig).
    r = client.get("/v1/models", headers={"Authorization": "Token abc"})
    assert r.status_code == 401


def test_static_ui_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "Chat" in r.text
