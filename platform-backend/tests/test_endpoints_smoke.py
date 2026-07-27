"""Smoke-Tests der Endpunkt-Verdrahtung: Routing + Auth-Gate + statisches UI.
Ohne DB — die geschuetzten Routen antworten 401, bevor sie die DB beruehren."""
# Die Dummy-Umgebung setzt conftest.py (wird vor den Testmodulen geladen);
# diese Tests treffen keinen DB-Pfad, der Pool oeffnet lazy.
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_protected_routes_require_auth():
    assert client.get("/v1/models").status_code == 401
    assert client.get("/v1/usage").status_code == 401
    assert client.get("/v1/conversations").status_code == 401
    assert client.get("/v1/agents").status_code == 401
    assert client.post("/v1/chat", json={"model": "x", "messages": [{"role": "user", "content": "hi"}]}).status_code == 401


def test_arbitrary_authorization_header_is_ignored_and_still_401():
    # Es gibt keinen Bearer-Pfad mehr -- require_principal liest den
    # Authorization-Header ueberhaupt nicht (nur noch das Session-Cookie).
    # Ein mitgeschickter Header aendert also nichts: ohne Cookie bleibt es
    # bei 401, ganz ohne DB-Zugriff.
    r = client.get("/v1/models", headers={"Authorization": "Token abc"})
    assert r.status_code == 401


def test_static_ui_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "Chat" in r.text
