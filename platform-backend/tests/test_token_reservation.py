"""Beweist, dass die atomare Token-Reservierung die TOCTOU-Luecke aus dem
alten Vorab-Check wirklich schliesst -- mit ECHTER Nebenlaeufigkeit (zwei
Threads, zwei eigene DB-Verbindungen), nicht nur sequenziellen Aufrufen (die
waeren auch mit dem alten Code schon korrekt gewesen; der Bug zeigte sich
nur bei echtem Race)."""
from __future__ import annotations

import os
import threading

import pytest

from app.completions import _reserve_tokens, _release_reservation
from app.db import tenant_tx

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


def _new_tenant(client, plan="free"):
    r = client.post(
        "/admin/provision",
        headers={"X-Admin-Token": "test-admin"},
        json={"tenant_name": "ConcurrencyT", "owner_email": "conc@example.ch", "plan_code": plan},
    )
    assert r.status_code == 200, r.text
    return r.json()["tenant_id"]


def test_concurrent_reservations_never_overshoot_limit(client):
    """free-Tarif: monthly_token_limit=100000. Zwei Threads reservieren
    gleichzeitig je 60000 -- zusammen 120000 > Limit. Die alte
    Vorab-Check-Logik haette BEIDE durchgelassen (beide sehen used=0 < Limit,
    bevor eine von beiden etwas schreibt). Die atomare Reservierung darf nur
    EINE durchlassen."""
    tenant_id = _new_tenant(client, "free")
    limit = 100_000
    per_call = 60_000

    results = []
    barrier = threading.Barrier(2)

    def worker():
        barrier.wait()  # so nah wie moeglich am selben Zeitpunkt starten
        with tenant_tx(tenant_id) as conn:
            ok = _reserve_tokens(conn, tenant_id, per_call, limit)
        results.append(ok)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert len(results) == 2
    assert sum(1 for ok in results if ok) == 1, (
        f"Erwartet: genau EINE der beiden gleichzeitigen Reservierungen "
        f"durfte durch (Summe waere {2*per_call} > Limit {limit}), "
        f"tatsaechlich: {results}"
    )

    # Reservierung tatsaechlich in der DB sichtbar (nicht nur im Rueckgabewert).
    with tenant_tx(tenant_id) as conn:
        row = conn.execute(
            "SELECT reserved_tokens FROM tenants WHERE id = %s", (tenant_id,)
        ).fetchone()
    assert row["reserved_tokens"] == per_call


def test_release_after_reserve_frees_quota_for_next_request(client):
    tenant_id = _new_tenant(client, "free")
    limit = 100_000
    estimate = 90_000

    with tenant_tx(tenant_id) as conn:
        assert _reserve_tokens(conn, tenant_id, estimate, limit) is True
        # Ein zweiter Aufruf ueber das verbleibende Kontingent hinaus scheitert.
        assert _reserve_tokens(conn, tenant_id, estimate, limit) is False

    with tenant_tx(tenant_id) as conn:
        _release_reservation(conn, tenant_id, estimate)

    # Nach Freigabe wieder moeglich.
    with tenant_tx(tenant_id) as conn:
        assert _reserve_tokens(conn, tenant_id, estimate, limit) is True


def test_reservation_plus_real_usage_both_count_toward_limit(client):
    """Reservierung UND bereits eingetragener echter Verbrauch zaehlen
    gemeinsam gegen das Limit -- nicht nur eines von beiden."""
    tenant_id = _new_tenant(client, "free")
    limit = 100_000

    with tenant_tx(tenant_id) as conn:
        conn.execute(
            "INSERT INTO usage_events (tenant_id, model, tokens_in, tokens_out) "
            "VALUES (%s, 'ollama/llama3.2', 60000, 0)",
            (tenant_id,),
        )

    with tenant_tx(tenant_id) as conn:
        # 60000 (echt) + 50000 (Reservierung) > 100000 -> abgelehnt.
        assert _reserve_tokens(conn, tenant_id, 50_000, limit) is False
        # 60000 (echt) + 30000 (Reservierung) <= 100000 -> erlaubt.
        assert _reserve_tokens(conn, tenant_id, 30_000, limit) is True
