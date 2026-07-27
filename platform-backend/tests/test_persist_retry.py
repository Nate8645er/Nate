"""Beweist die README-dokumentierte Luecke ist teilweise geschlossen:
transiente Persistenz-Fehler NACH einem erfolgreichen Gateway-Aufruf
(Verbindungsabbruch, Pool-Spitze) werden jetzt innerhalb derselben Anfrage
wiederholt, statt den bereits real entstandenen Verbrauch sofort zu
verlieren. Kein Test der DB-Schicht selbst (die ist schon anderswo
getestet) -- reiner Test der Retry-Logik in _persist_and_release_with_retry."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest
from fastapi import HTTPException

import app.completions as completions


@dataclass
class _FakePrincipal:
    tenant_id: str = "t1"
    stripe_customer_id: str | None = None


async def _no_op_sleep(*_args):
    """Ersetzt asyncio.sleep in den Retry-Tests, damit sie nicht wirklich
    warten -- separat definiert statt als Lambda um asyncio.sleep(0), weil
    completions.asyncio dasselbe globale asyncio-Modul ist: ein Lambda, das
    selbst asyncio.sleep aufruft, wuerde die eigene Ersetzung rekursiv
    aufrufen (RecursionError, real aufgetreten beim ersten Versuch)."""
    return None


def test_succeeds_on_first_try_without_retry(monkeypatch):
    calls = []

    def fake_persist(principal, conversation_id, last_user, model, answer, tokens_in, tokens_out, reserve_estimate):
        calls.append(1)
        return "conv-1"

    monkeypatch.setattr(completions, "_persist_and_release", fake_persist)
    result = asyncio.run(completions._persist_and_release_with_retry(
        _FakePrincipal(), None, "hi", "m", "answer", 1, 1, 10,
    ))
    assert result == "conv-1"
    assert len(calls) == 1


def test_recovers_after_transient_failures(monkeypatch):
    """Erste zwei Versuche scheitern (simulierter DB-Verbindungsabbruch),
    dritter klappt -- die Antwort geht NICHT verloren."""
    attempts = []

    def flaky_persist(principal, conversation_id, last_user, model, answer, tokens_in, tokens_out, reserve_estimate):
        attempts.append(1)
        if len(attempts) < 3:
            raise ConnectionError("DB-Verbindung abgebrochen (simuliert)")
        return "conv-recovered"

    monkeypatch.setattr(completions, "_persist_and_release", flaky_persist)
    monkeypatch.setattr(completions.asyncio, "sleep", _no_op_sleep)  # Test nicht wirklich warten lassen

    result = asyncio.run(completions._persist_and_release_with_retry(
        _FakePrincipal(), None, "hi", "m", "answer", 1, 1, 10,
    ))
    assert result == "conv-recovered"
    assert len(attempts) == 3


def test_raises_after_exhausting_all_retries(monkeypatch):
    attempts = []

    def always_fails(principal, conversation_id, last_user, model, answer, tokens_in, tokens_out, reserve_estimate):
        attempts.append(1)
        raise ConnectionError("DB dauerhaft weg (simuliert)")

    monkeypatch.setattr(completions, "_persist_and_release", always_fails)
    monkeypatch.setattr(completions.asyncio, "sleep", _no_op_sleep)

    with pytest.raises(ConnectionError):
        asyncio.run(completions._persist_and_release_with_retry(
            _FakePrincipal(), None, "hi", "m", "answer", 1, 1, 10,
        ))
    assert len(attempts) == completions._PERSIST_RETRY_ATTEMPTS


def test_http_exception_is_also_retried_and_can_still_raise(monkeypatch):
    """Auch ein HTTPException (z.B. 404 Konversation nicht gefunden) aus der
    Persistenz-Transaktion wird als Fehler behandelt und nach erfolglosen
    Versuchen weitergereicht -- kein stiller Datenverlust."""
    def always_404(*a, **kw):
        raise HTTPException(status_code=404, detail="Konversation nicht gefunden")

    monkeypatch.setattr(completions, "_persist_and_release", always_404)
    monkeypatch.setattr(completions.asyncio, "sleep", _no_op_sleep)

    with pytest.raises(HTTPException):
        asyncio.run(completions._persist_and_release_with_retry(
            _FakePrincipal(), None, "hi", "m", "answer", 1, 1, 10,
        ))
