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


async def _provision(client: httpx.AsyncClient, admin_token: str, n: int) -> list[str]:
    keys = []
    for i in range(n):
        r = await client.post(
            "/admin/provision",
            headers={"X-Admin-Token": admin_token},
            json={"tenant_name": f"load{i}", "owner_email": f"load{i}@example.ch", "plan_code": "pro"},
        )
        r.raise_for_status()
        keys.append(r.json()["api_key"])
    return keys


async def _worker(client: httpx.AsyncClient, key: str, path: str, n: int, latencies: list[float]) -> int:
    errors = 0
    headers = {"Authorization": "Bearer " + key}
    for _ in range(n):
        t0 = time.perf_counter()
        try:
            r = await client.get(path, headers=headers)
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
    async with httpx.AsyncClient(transport=transport, base_url="http://loadtest") as client:
        keys = await _provision(client, admin_token, args.concurrency)

        per_worker = max(1, args.requests // args.concurrency)
        latencies: list[float] = []
        all_latencies: list[list[float]] = [[] for _ in range(args.concurrency)]

        t_start = time.perf_counter()
        errors = await asyncio.gather(*[
            _worker(client, keys[i], args.path, per_worker, all_latencies[i])
            for i in range(args.concurrency)
        ])
        wall = time.perf_counter() - t_start

        for lst in all_latencies:
            latencies.extend(lst)
        latencies.sort()
        total_errors = sum(errors)
        total_requests = len(latencies)

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
