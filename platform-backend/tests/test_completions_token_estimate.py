"""Deckt den in README dokumentierten Luecken-Punkt ab: Gateways, die kein
usage-Objekt liefern (z.B. manche lokalen Ollama-Antworten), sollen NICHT
stillschweigend 0 Tokens zaehlen -- sonst zaehlt der Verbrauch nie gegen das
Monats-Limit."""
from __future__ import annotations

import os

import httpx
import pytest

from app.completions import _estimate_tokens

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")


def test_estimate_tokens_empty_text_is_zero():
    assert _estimate_tokens("") == 0


def test_estimate_tokens_nonempty_short_text_is_at_least_one():
    assert _estimate_tokens("a") == 1
    assert _estimate_tokens("hi") == 1


def test_estimate_tokens_scales_with_length():
    assert _estimate_tokens("a" * 40) == 10
    assert _estimate_tokens("a" * 400) == 100


@pytest.mark.skipif(not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)")
class TestMissingUsageFallback:
    class _FakeAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, json=None, headers=None):
            # Absichtlich KEIN "usage"-Feld -- genau der Fall, den manche
            # Ollama-Antworten je nach LiteLLM-Version liefern.
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Hallo, wie kann ich helfen?"}}]},
            )

    def test_missing_usage_object_falls_back_to_estimate(self, client, prov, monkeypatch):
        monkeypatch.setattr("app.completions.httpx.AsyncClient", self._FakeAsyncClient)
        key = prov("starter")
        h = {"Authorization": "Bearer " + key}
        r = client.post(
            "/v1/chat",
            headers=h,
            json={"model": "ollama/llama3.2", "messages": [{"role": "user", "content": "Hallo, wie geht es dir heute?"}]},
        )
        assert r.status_code == 200, r.text
        usage = r.json()["usage"]
        assert usage["tokens_in"] > 0
        assert usage["tokens_out"] > 0

    def test_estimated_usage_counts_toward_monthly_limit(self, client, prov, monkeypatch):
        """Beweist den eigentlichen Zweck: geschaetzter Verbrauch zaehlt
        wirklich gegen das Limit, nicht nur kosmetisch in der Antwort."""
        monkeypatch.setattr("app.completions.httpx.AsyncClient", self._FakeAsyncClient)
        key = prov("free")  # monthly_token_limit = 100000
        h = {"Authorization": "Bearer " + key}

        r1 = client.post(
            "/v1/chat", headers=h,
            json={"model": "ollama/llama3.2", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert r1.status_code == 200
        used_after_one = r1.json()["usage"]["tokens_in"] + r1.json()["usage"]["tokens_out"]
        assert used_after_one > 0

        usage = client.get("/v1/usage", headers=h).json()
        assert usage["month"]["tokens_total"] == used_after_one
