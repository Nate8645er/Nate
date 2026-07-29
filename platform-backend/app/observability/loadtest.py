"""Kleiner Lasttest (Phase 8 · Hardening).

Misst Durchsatz und Latenz-Perzentile eines HTTP-Endpunkts unter kontrollierter
Nebenläufigkeit. Zweck: eine ehrliche Baseline (p50/p95/p99) und das Aufdecken
von Fehlern unter Last — kein Ersatz für ein echtes Lastwerkzeug (k6/Locust),
aber dependency-arm und im Repo lauffähig.

Die Perzentil-/Zusammenfassungslogik ist rein und offline getestet; der Runner
nutzt httpx.AsyncClient. Ehrlich: gezählt werden auch Fehler (non-2xx/Exceptions).

CLI:  python -m app.observability.loadtest http://127.0.0.1:8000/health/live -n 500 -c 20
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


def percentile(sorted_values: list[float], p: float) -> float:
    """Linear interpoliertes Perzentil (p in [0,100]). Erwartet SORTIERTE Werte."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (p / 100) * (len(sorted_values) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = rank - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


@dataclass(frozen=True)
class LoadResult:
    total: int
    ok: int
    failed: int
    duration_s: float
    latencies_ms: list[float]

    @property
    def rps(self) -> float:
        return self.total / self.duration_s if self.duration_s > 0 else 0.0

    def summary(self) -> dict:
        lat = sorted(self.latencies_ms)
        return {
            "requests": self.total,
            "ok": self.ok,
            "failed": self.failed,
            "duration_s": round(self.duration_s, 3),
            "rps": round(self.rps, 1),
            "latency_ms": {
                "p50": round(percentile(lat, 50), 2),
                "p95": round(percentile(lat, 95), 2),
                "p99": round(percentile(lat, 99), 2),
                "max": round(lat[-1], 2) if lat else 0.0,
            },
        }


def summarize(results: list[tuple[bool, float]], duration_s: float) -> LoadResult:
    """Baut aus (ok, latency_ms)-Paaren eine Zusammenfassung. Rein/testbar."""
    ok = sum(1 for good, _ in results if good)
    lat = [ms for good, ms in results if good]
    return LoadResult(
        total=len(results), ok=ok, failed=len(results) - ok,
        duration_s=duration_s, latencies_ms=lat,
    )


async def run_load(
    url: str,
    n_requests: int = 200,
    concurrency: int = 20,
    timeout_s: float = 5.0,
    client=None,
) -> LoadResult:
    """Feuert `n_requests` GETs mit begrenzter Nebenläufigkeit gegen `url`."""
    import httpx

    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=timeout_s)
    sem = asyncio.Semaphore(concurrency)
    results: list[tuple[bool, float]] = []

    async def one() -> None:
        async with sem:
            start = time.perf_counter()
            try:
                resp = await client.get(url)
                ok = 200 <= resp.status_code < 300
            except Exception:  # noqa: BLE001 — Fehler zählen, nicht werfen
                ok = False
            results.append((ok, (time.perf_counter() - start) * 1000))

    wall_start = time.perf_counter()
    try:
        await asyncio.gather(*(one() for _ in range(n_requests)))
    finally:
        if owns_client:
            await client.aclose()
    return summarize(results, time.perf_counter() - wall_start)


def _main(argv: list[str]) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Kleiner HTTP-Lasttest")
    parser.add_argument("url")
    parser.add_argument("-n", "--requests", type=int, default=200)
    parser.add_argument("-c", "--concurrency", type=int, default=20)
    args = parser.parse_args(argv)
    result = asyncio.run(run_load(args.url, args.requests, args.concurrency))
    print(json.dumps(result.summary(), indent=2, ensure_ascii=False))
    return 0 if result.failed == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(_main(sys.argv[1:]))
