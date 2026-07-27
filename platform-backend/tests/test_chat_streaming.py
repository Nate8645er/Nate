"""Beweist die Streaming-Unterstuetzung (stream=true) gegen eine echte
Postgres-DB, mit einem gefaelschten SSE-Gateway (kein echtes LiteLLM in
dieser Sandbox) -- prueft den tatsaechlichen Code-Pfad in
app/completions.py::stream_chat, nicht nur die Attrappe selbst."""
from __future__ import annotations

import json
import os

import pytest

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


def _sse_lines(chunks, with_usage=True):
    for c in chunks:
        yield f"data: {json.dumps(c)}"
    if with_usage:
        yield "data: " + json.dumps({
            "choices": [], "usage": {"prompt_tokens": 11, "completion_tokens": 22},
        })
    yield "data: [DONE]"


class _FakeStreamResponse:
    def __init__(self, lines, status_code=200):
        self._lines = lines
        self.status_code = status_code

    async def aiter_lines(self):
        for line in self._lines:
            yield line

    async def aread(self):
        return b"error body"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _FakeAsyncClient:
    def __init__(self, lines, status_code=200):
        self._lines = lines
        self._status_code = status_code

    def __call__(self, *a, **kw):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def stream(self, method, url, json=None, headers=None):
        return _FakeStreamResponse(list(self._lines), self._status_code)


def _fake_client_factory(chunks, with_usage=True, status_code=200):
    lines = list(_sse_lines(chunks, with_usage=with_usage)) if status_code < 400 else []
    return _FakeAsyncClient(lines, status_code=status_code)


def test_stream_forwards_chunks_and_persists_real_usage(client, prov, monkeypatch):
    chunks = [
        {"choices": [{"delta": {"content": "Hallo"}}]},
        {"choices": [{"delta": {"content": ", Welt!"}}]},
    ]
    fake = _fake_client_factory(chunks, with_usage=True)
    monkeypatch.setattr("app.completions.httpx.AsyncClient", lambda *a, **kw: fake)

    key = prov("starter")
    h = {"Authorization": "Bearer " + key}
    with client.stream(
        "POST", "/v1/chat", headers=h,
        json={"model": "ollama/llama3.2", "messages": [{"role": "user", "content": "Hi"}], "stream": True},
    ) as r:
        assert r.status_code == 200
        body = b"".join(r.iter_bytes()).decode()

    assert "Hallo" in body
    assert ", Welt!" in body
    assert "[DONE]" in body

    usage = client.get("/v1/usage", headers=h).json()
    # Echte usage-Werte aus dem letzten Chunk (11+22=33), nicht geschaetzt.
    assert usage["month"]["tokens_total"] == 33


def test_stream_without_usage_object_falls_back_to_estimate(client, prov, monkeypatch):
    chunks = [{"choices": [{"delta": {"content": "Hallo, wie kann ich helfen?"}}]}]
    fake = _fake_client_factory(chunks, with_usage=False)
    monkeypatch.setattr("app.completions.httpx.AsyncClient", lambda *a, **kw: fake)

    key = prov("starter")
    h = {"Authorization": "Bearer " + key}
    with client.stream(
        "POST", "/v1/chat", headers=h,
        json={"model": "ollama/llama3.2", "messages": [{"role": "user", "content": "Hi"}], "stream": True},
    ) as r:
        assert r.status_code == 200
        list(r.iter_bytes())

    usage = client.get("/v1/usage", headers=h).json()
    assert usage["month"]["tokens_total"] > 0


def test_stream_releases_reservation_after_completion(client, prov, monkeypatch):
    """Nach einem abgeschlossenen Stream darf reserved_tokens nicht mehr
    hoch bleiben -- sonst wuerde jeder Stream permanent Kontingent
    blockieren."""
    from app.db import tenant_tx

    chunks = [{"choices": [{"delta": {"content": "ok"}}]}]
    fake = _fake_client_factory(chunks, with_usage=True)
    monkeypatch.setattr("app.completions.httpx.AsyncClient", lambda *a, **kw: fake)

    prov_resp = client.post(
        "/admin/provision", headers={"X-Admin-Token": "test-admin"},
        json={"tenant_name": "StreamT", "owner_email": "stream@example.ch", "plan_code": "starter"},
    )
    tenant_id = prov_resp.json()["tenant_id"]
    key = prov_resp.json()["api_key"]
    h = {"Authorization": "Bearer " + key}

    with client.stream(
        "POST", "/v1/chat", headers=h,
        json={"model": "ollama/llama3.2", "messages": [{"role": "user", "content": "Hi"}], "stream": True},
    ) as r:
        list(r.iter_bytes())

    with tenant_tx(tenant_id) as conn:
        row = conn.execute("SELECT reserved_tokens FROM tenants WHERE id = %s", (tenant_id,)).fetchone()
    assert row["reserved_tokens"] == 0


def test_stream_returns_conversation_id_for_continuation(client, prov, monkeypatch):
    """Regression fuer den Bug, den ultra-architect gefunden hat: der Stream-
    Pfad gab die conversation_id nirgends an den Client zurueck, weshalb jede
    Nachricht serverseitig eine NEUE Konversation anlegte statt eine
    bestehende fortzusetzen. Beweist beide Haelften: (1) die erste Antwort
    enthaelt einen conversation_id-Chunk, (2) eine zweite Nachricht MIT
    dieser ID haengt wirklich an dieselbe Konversation an (4 Nachrichten,
    nicht 2+2 in getrennten Konversationen)."""
    import re

    def _stream_one(msg):
        chunks = [{"choices": [{"delta": {"content": "Antwort zu: " + msg}}]}]
        fake = _fake_client_factory(chunks, with_usage=True)
        monkeypatch.setattr("app.completions.httpx.AsyncClient", lambda *a, **kw: fake)

    key = prov("starter")
    h = {"Authorization": "Bearer " + key}

    _stream_one("Erste")
    with client.stream(
        "POST", "/v1/chat", headers=h,
        json={"model": "ollama/llama3.2", "messages": [{"role": "user", "content": "Erste"}], "stream": True},
    ) as r:
        assert r.status_code == 200
        body = b"".join(r.iter_bytes()).decode()

    ids = re.findall(r'"conversation_id":\s*"([0-9a-f-]{36})"', body)
    assert ids, "kein conversation_id-Chunk im Stream gefunden"
    conv_id = ids[0]
    # Alle Chunks (falls mehrere) muessen dieselbe ID tragen -- keine zweite
    # Konversation waehrend desselben Streams.
    assert all(i == conv_id for i in ids)

    _stream_one("Zweite")
    with client.stream(
        "POST", "/v1/chat", headers=h,
        json={
            "model": "ollama/llama3.2",
            "messages": [{"role": "user", "content": "Erste"}, {"role": "user", "content": "Zweite"}],
            "conversation_id": conv_id,
            "stream": True,
        },
    ) as r2:
        assert r2.status_code == 200
        list(r2.iter_bytes())

    conv = client.get(f"/v1/conversations/{conv_id}", headers=h)
    assert conv.status_code == 200
    messages = conv.json()["messages"]
    assert len(messages) == 4, "beide Nachrichten muessen in DERSELBEN Konversation gelandet sein"


def test_stream_unregistered_model_rejected_before_streaming_starts(client, prov):
    """Ohne Gateway-Mock: ein nicht registriertes Modell muss VOR jedem
    Streaming-Versuch mit 403 abgelehnt werden (Modellvalidierung passiert
    vor stream_chat)."""
    key = prov("starter")
    h = {"Authorization": "Bearer " + key}
    r = client.post(
        "/v1/chat", headers=h,
        json={"model": "erfundenes/modell", "messages": [{"role": "user", "content": "Hi"}], "stream": True},
    )
    assert r.status_code == 403
