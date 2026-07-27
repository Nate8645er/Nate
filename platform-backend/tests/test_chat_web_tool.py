"""Beweist den optionalen web_fetch-Tool-Ablauf im nicht-streamenden
/v1/chat-Pfad (app/completions.py::run_chat) gegen eine echte Postgres-DB,
mit einem gefaelschten (nicht-streamenden) Gateway. `web_fetch` selbst wird
hier NICHT erneut auf SSRF getestet -- das leistet bereits erschoepfend
tests/test_web_fetch_tool.py -- sondern nur die Orchestrierung: Opt-in-Flag,
Tool-Call-Ausfuehrung, Nachrichtenaufbau fuer den zweiten Rundgang, die
harten Obergrenzen (max. 3 Tool-Calls, max. 2 Gateway-Rundgaenge)."""
from __future__ import annotations

import json
import os

import httpx
import pytest

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


class _QueuedGateway:
    """Fake fuer httpx.AsyncClient, nur fuer den nicht-streamenden .post()-
    Pfad (_post_gateway) -- zeichnet jeden gesendeten Payload auf und
    beantwortet Aufrufe der Reihe nach mit den vorbereiteten Antworten."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests: list[dict] = []

    def __call__(self, *a, **kw):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, json=None, headers=None):  # noqa: A002 -- passt zu httpx-Signatur
        self.requests.append(json)
        body = self.responses.pop(0)
        return httpx.Response(200, json=body)


def _msg(content=None, tool_calls=None):
    m = {"role": "assistant"}
    if content is not None:
        m["content"] = content
    if tool_calls is not None:
        m["tool_calls"] = tool_calls
    return m


def _tool_call(call_id, url):
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": "web_fetch", "arguments": json.dumps({"url": url})},
    }


def test_web_tool_disabled_by_default_unchanged_behavior(client, prov, monkeypatch):
    fake = _QueuedGateway([
        {"choices": [{"message": _msg("Hallo!")}], "usage": {"prompt_tokens": 5, "completion_tokens": 3}},
    ])
    monkeypatch.setattr("app.completions.httpx.AsyncClient", fake)

    prov("starter")
    r = client.post(
        "/v1/chat",
        json={"model": "ollama/llama3.2", "messages": [{"role": "user", "content": "Hi"}]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["answer"] == "Hallo!"

    assert len(fake.requests) == 1, "ohne enable_web_tool darf es nur EINEN Gateway-Rundgang geben"
    assert "tools" not in fake.requests[0]
    assert "tool_choice" not in fake.requests[0]


def test_web_tool_enabled_attaches_schema_when_model_uses_no_tool(client, prov, monkeypatch):
    fake = _QueuedGateway([
        {"choices": [{"message": _msg("Kein Tool noetig.")}], "usage": {"prompt_tokens": 5, "completion_tokens": 3}},
    ])
    monkeypatch.setattr("app.completions.httpx.AsyncClient", fake)

    prov("starter")
    r = client.post(
        "/v1/chat",
        json={
            "model": "ollama/llama3.2",
            "messages": [{"role": "user", "content": "Hi"}],
            "enable_web_tool": True,
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["answer"] == "Kein Tool noetig."

    assert len(fake.requests) == 1
    sent = fake.requests[0]
    assert sent["tool_choice"] == "auto"
    assert sent["tools"][0]["function"]["name"] == "web_fetch"


def test_web_tool_call_runs_and_triggers_second_gateway_round(client, prov, monkeypatch):
    first = _msg(tool_calls=[_tool_call("call_1", "http://example.com/")])
    fake = _QueuedGateway([
        {"choices": [{"message": first}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}},
        {
            "choices": [{"message": _msg("Auf der Seite steht: Hallo Welt.")}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 8},
        },
    ])
    monkeypatch.setattr("app.completions.httpx.AsyncClient", fake)

    calls = []

    async def _fake_web_fetch(url):
        calls.append(url)
        return "Hallo Welt."

    monkeypatch.setattr("app.completions.web_fetch", _fake_web_fetch)

    prov("starter")
    r = client.post(
        "/v1/chat",
        json={
            "model": "ollama/llama3.2",
            "messages": [{"role": "user", "content": "Was steht auf http://example.com/?"}],
            "enable_web_tool": True,
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["answer"] == "Auf der Seite steht: Hallo Welt."

    # web_fetch wurde genau einmal mit der vom Modell angeforderten URL
    # aufgerufen.
    assert calls == ["http://example.com/"]

    # Genau zwei Gateway-Rundgaenge -- nicht mehr (harte Obergrenze).
    assert len(fake.requests) == 2

    # Runde 1: Tools angehaengt.
    assert fake.requests[0]["tool_choice"] == "auto"

    # Runde 2: KEIN "tools" mehr (Budget aufgebraucht, erzwingt eine
    # endgueltige Antwort), aber die Assistant-Nachricht mit tool_calls UND
    # das Tool-Ergebnis sind Teil der gesendeten Nachrichten.
    second_messages = fake.requests[1]["messages"]
    assert "tools" not in fake.requests[1]
    roles = [m["role"] for m in second_messages]
    assert "tool" in roles
    tool_msg = next(m for m in second_messages if m["role"] == "tool")
    assert tool_msg["tool_call_id"] == "call_1"
    assert tool_msg["content"] == "Hallo Welt."

    # Verbrauch aus BEIDEN Rundgaengen zaehlt (10+20 in, 5+8 out = 43 total).
    usage = client.get("/v1/usage").json()
    assert usage["month"]["tokens_total"] == 43


def test_web_tool_calls_capped_at_three_per_request(client, prov, monkeypatch):
    many_calls = [_tool_call(f"call_{i}", f"http://example.com/{i}") for i in range(5)]
    first = _msg(tool_calls=many_calls)
    fake = _QueuedGateway([
        {"choices": [{"message": first}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}},
        {"choices": [{"message": _msg("Fertig.")}], "usage": {"prompt_tokens": 1, "completion_tokens": 1}},
    ])
    monkeypatch.setattr("app.completions.httpx.AsyncClient", fake)

    calls = []

    async def _fake_web_fetch(url):
        calls.append(url)
        return f"Inhalt von {url}"

    monkeypatch.setattr("app.completions.web_fetch", _fake_web_fetch)

    prov("starter")
    r = client.post(
        "/v1/chat",
        json={
            "model": "ollama/llama3.2",
            "messages": [{"role": "user", "content": "Lies mir 5 Seiten vor"}],
            "enable_web_tool": True,
        },
    )
    assert r.status_code == 200, r.text

    # Trotz 5 angeforderter Tool-Calls: hoechstens 3 wurden tatsaechlich
    # ausgefuehrt (harte Obergrenze im Code, nicht nur Kommentar).
    assert len(calls) == 3

    second_messages = fake.requests[1]["messages"]
    tool_msgs = [m for m in second_messages if m["role"] == "tool"]
    assert len(tool_msgs) == 3


def test_web_tool_ignored_on_streaming_path(client, prov, monkeypatch):
    """enable_web_tool wird im SSE-Streaming-Pfad bewusst ignoriert (siehe
    README/CLAUDE.md) -- kein tools-Feld im gestreamten Gateway-Payload."""
    sent_payloads = []

    class _FakeStreamResponse:
        status_code = 200

        async def aiter_lines(self):
            yield "data: " + json.dumps({
                "choices": [{"delta": {"content": "ok"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            })
            yield "data: [DONE]"

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

    class _FakeStreamClient:
        def __call__(self, *a, **kw):
            return self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        def stream(self, method, url, json=None, headers=None):
            sent_payloads.append(json)
            return _FakeStreamResponse()

    monkeypatch.setattr("app.completions.httpx.AsyncClient", _FakeStreamClient())

    prov("starter")
    with client.stream(
        "POST", "/v1/chat",
        json={
            "model": "ollama/llama3.2",
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": True,
            "enable_web_tool": True,
        },
    ) as r:
        assert r.status_code == 200
        list(r.iter_bytes())

    assert len(sent_payloads) == 1
    assert "tools" not in sent_payloads[0]
