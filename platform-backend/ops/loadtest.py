#!/usr/bin/env python3
"""Lasttest fuer Produkt A (Phase 7 DoD).

Treibt echte Requests gegen die echte FastAPI-App (ASGI in-process, per
httpx.ASGITransport) — durchlaeuft Auth, RLS-gebundene Datenbankzugriffe
und JSON-Serialisierung wie im echten Betrieb. Bewusst NICHT durch einen
echten uvicorn-Prozess/Netzwerk-Stack getunnelt: das haette in dieser
Umgebung keinen Mehrwert (kein Reverse-Proxy, keine echte Netzwerklatenz
zu testen) und macht den Test overhead-frei genug, um die Anwendungslogik
selbst zu belasten.

Getestete Pfade: GET /v1/models, GET /v1/usage — die haeufigsten Lesepfade
(Dashboard/UI-Polling). /v1/chat bewusst ausgeklammert: braucht ein
laufendes LiteLLM-Gateway, das hier nicht verfuegbar ist.

Nutzung (braucht eine laufende Postgres-Testdatenbank, siehe README):
  DATABASE_URL=postgresql://app_rw:...@host/db \
  MIGRATE_DATABASE_URL=postgresql://postgres:...@host/db \
  ADMIN_TOKEN=... \
    python ops/loadtest.py --concurrency 20 --requests 500
"""
from __future__ import annotations

import argparse
import asyncio
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx  # noqa: E402


async def _provision_and_login(transport: httpx.ASGITransport, admin_token: str, i: int) -> httpx.AsyncClient:
    """Legt Mandant `i` per /admin/provision an (jetzt mit Pflicht-Passwort,
    kein API-Key mehr) und meldet eine EIGENE httpx.AsyncClient-Instanz per
    /v1/auth/login an. Jeder Worker braucht seinen eigenen Client, weil das
    Session-Cookie in dessen Cookie-Jar liegt -- ein gemeinsam genutzter
    Client wuerde mit jedem Login die Session des vorherigen Mandanten
    ueberschreiben."""
    email = f"load{i}@example.ch"
    password = "loadtest-password-1"
    client = httpx.AsyncClient(transport=transport, base_url="https://loadtest")
    r = await client.post(
        "/admin/provision",
        headers={"X-Admin-Token": admin_token},
        json={"tenant_name": f"load{i}", "owner_email": email, "plan_code": "pro", "password": password},
    )
    r.raise_for_status()
    login = await client.post("/v1/auth/login", json={"email": email, "password": password})
    login.raise_for_status()
    return client


async def _worker(client: httpx.AsyncClient, path: str, n: int, latencies: list[float]) -> int:
    errors = 0
    for _ in range(n):
        t0 = time.perf_counter()
        try:
            r = await client.get(path)
            latencies.append(time.perf_counter() - t0)
            if r.status_code != 200:
                errors += 1
        except Exception:
            latencies.append(time.perf_counter() - t0)
            errors += 1
    return errors


def _percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, int(len(sorted_vals) * p))
    return sorted_vals[idx]


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=20)
    ap.add_argument("--requests", type=int, default=500, help="Gesamtzahl Requests")
    ap.add_argument("--path", default="/v1/models")
    args = ap.parse_args()

    admin_token = os.environ.get("ADMIN_TOKEN", "loadtest-admin")
    os.environ.setdefault("ADMIN_TOKEN", admin_token)

    from app.db import migrate
    migrate()

    from app.main import app

    transport = httpx.ASGITransport(app=app)
    # https-Basis-URL: die Session-Cookies aus app/auth.py setzen bewusst das
    # Secure-Flag -- httpx haengt Secure-Cookies nur an Requests mit
    # https-Schema an (siehe derselbe Kommentar in tests/conftest.py).
    clients = await asyncio.gather(*[
        _provision_and_login(transport, admin_token, i) for i in range(args.concurrency)
    ])
    try:
        per_worker = max(1, args.requests // args.concurrency)
        latencies: list[float] = []
        all_latencies: list[list[float]] = [[] for _ in range(args.concurrency)]

        t_start = time.perf_counter()
        errors = await asyncio.gather(*[
            _worker(clients[i], args.path, per_worker, all_latencies[i])
            for i in range(args.concurrency)
        ])
        wall = time.perf_counter() - t_start

        for lst in all_latencies:
            latencies.extend(lst)
        latencies.sort()
        total_errors = sum(errors)
        total_requests = len(latencies)
    finally:
        await asyncio.gather(*(c.aclose() for c in clients))

    print(f"Pfad:            {args.path}")
    print(f"Nebenlaeufigkeit: {args.concurrency}")
    print(f"Requests gesamt:  {total_requests}")
    print(f"Fehler:           {total_errors}")
    print(f"Wandzeit:         {wall:.2f}s")
    print(f"Durchsatz:        {total_requests / wall:.1f} req/s")
    if latencies:
        print(f"Latenz p50:       {statistics.median(latencies)*1000:.1f} ms")
        print(f"Latenz p95:       {_percentile(latencies, 0.95)*1000:.1f} ms")
        print(f"Latenz p99:       {_percentile(latencies, 0.99)*1000:.1f} ms")
        print(f"Latenz max:       {max(latencies)*1000:.1f} ms")


if __name__ == "__main__":
    asyncio.run(main())
