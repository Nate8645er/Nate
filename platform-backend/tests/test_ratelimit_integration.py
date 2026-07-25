"""Beweist, dass /v1/chat wirklich gedrosselt wird (nicht nur der Limiter
isoliert). Laeuft nur mit PLATFORM_TEST_DATABASE_URL."""
from __future__ import annotations

import os

import pytest

from app.ratelimit import chat_limiter

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


@pytest.fixture(autouse=True)
def _reset_limiter():
    chat_limiter.reset()
    yield
    chat_limiter.reset()


def test_chat_route_is_rate_limited(client, prov, monkeypatch):
    monkeypatch.setattr(chat_limiter, "max_calls", 2)
    key = prov("free")
    h = {"Authorization": "Bearer " + key}
    body = {"model": "ollama/llama3.2", "messages": [{"role": "user", "content": "hi"}]}

    # Die ersten 2 Aufrufe passieren den Limiter (scheitern danach am fehlenden
    # Gateway mit 502 -> beweist, dass sie den Limiter durchlaufen haben).
    for _ in range(2):
        r = client.post("/v1/chat", headers=h, json=body)
        assert r.status_code == 502

    # Der dritte wird VOM LIMITER abgewiesen, bevor das Gateway ueberhaupt
    # kontaktiert wird.
    r3 = client.post("/v1/chat", headers=h, json=body)
    assert r3.status_code == 429
    assert "Retry-After" in r3.headers
