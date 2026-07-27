"""Testet app/stripe_usage.py mit einem gefaelschten HTTP-Client -- kein
echter Stripe-Account/Secret-Key existiert in dieser Umgebung, daher kann
nur die Aufrufstruktur (Endpoint, Feldnamen, Auth) verifiziert werden, nicht
die tatsaechliche Stripe-API-Kompatibilitaet.

Reine `asyncio.run()`-Wrapper statt pytest-asyncio/anyio-Testfunktionen --
dieses Projekt hat bisher keinen Async-Test-Runner konfiguriert (alle
anderen Async-Pfade laufen ueber TestClient, das sync wrapped); ein neues
Plugin nur fuer diese Datei waere unnoetiger Umfang."""
from __future__ import annotations

import asyncio

import httpx
import pytest

import app.stripe_usage as stripe_usage


class _CapturingClient:
    """Zeichnet den Aufruf auf und liefert eine feste Antwort -- gleiche
    Attrappe wie in den anderen Tests dieser Sitzung (composio, Gateway)."""

    calls = []

    def __init__(self, status_code=200):
        self._status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, auth=None, data=None):
        type(self).calls.append({"url": url, "auth": auth, "data": data})
        return httpx.Response(self._status_code, text="{}")


@pytest.fixture(autouse=True)
def _reset_calls():
    _CapturingClient.calls = []
    yield


def test_noop_without_secret_key(monkeypatch):
    monkeypatch.setattr(stripe_usage.settings, "stripe_secret_key", "")
    monkeypatch.setattr(stripe_usage.httpx, "AsyncClient", lambda *a, **kw: _CapturingClient())
    asyncio.run(stripe_usage.report_usage("cus_123", 1000))
    assert _CapturingClient.calls == []


def test_noop_without_customer_id(monkeypatch):
    monkeypatch.setattr(stripe_usage.settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(stripe_usage.httpx, "AsyncClient", lambda *a, **kw: _CapturingClient())
    asyncio.run(stripe_usage.report_usage(None, 1000))
    assert _CapturingClient.calls == []


def test_noop_for_zero_tokens(monkeypatch):
    monkeypatch.setattr(stripe_usage.settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(stripe_usage.httpx, "AsyncClient", lambda *a, **kw: _CapturingClient())
    asyncio.run(stripe_usage.report_usage("cus_123", 0))
    assert _CapturingClient.calls == []


def test_reports_with_correct_shape(monkeypatch):
    monkeypatch.setattr(stripe_usage.settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(stripe_usage.httpx, "AsyncClient", lambda *a, **kw: _CapturingClient())
    asyncio.run(stripe_usage.report_usage("cus_123", 4200))

    assert len(_CapturingClient.calls) == 1
    call = _CapturingClient.calls[0]
    assert call["url"] == "https://api.stripe.com/v1/billing/meter_events"
    assert call["auth"] == ("sk_test_fake", "")
    assert call["data"]["event_name"] == "platform_tokens"
    assert call["data"]["payload[stripe_customer_id]"] == "cus_123"
    assert call["data"]["payload[value]"] == "4200"


def test_http_error_status_does_not_raise(monkeypatch):
    monkeypatch.setattr(stripe_usage.settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(stripe_usage.httpx, "AsyncClient", lambda *a, **kw: _CapturingClient(status_code=400))
    asyncio.run(stripe_usage.report_usage("cus_123", 1000))  # darf nicht werfen


def test_connection_error_does_not_raise(monkeypatch):
    class _FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **kw):
            raise httpx.ConnectError("kein Netz (simuliert)")

    monkeypatch.setattr(stripe_usage.settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(stripe_usage.httpx, "AsyncClient", lambda *a, **kw: _FailingClient())
    asyncio.run(stripe_usage.report_usage("cus_123", 1000))  # darf nicht werfen
