"""HTTP-Observability (Phase 8 · Hardening).

Ergänzt die vorhandenen Compute-Gauges (`app/compute/metrics.py`) um
Anwendungs-Metriken auf Request-Ebene: Zähler pro Methode/Pfad/Status und ein
Latenz-Histogramm. Eine ASGI-Middleware misst jeden Request; `render_app_metrics`
liefert das Prometheus-Textformat für den `/metrics`-Endpunkt.

Bewusst mit EIGENER `CollectorRegistry` (nicht die globale `REGISTRY`), damit
Tests isoliert sind und mehrere App-Instanzen im selben Prozess kollisionsfrei
bleiben. Rein und ohne laufenden Scrape testbar.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest


class HttpMetrics:
    """Kapselt die Request-Metriken in einer eigenen Registry."""

    #: Grenzen in Sekunden — vom schnellen Health bis zu langsamen LLM-Calls.
    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        self.registry = registry or CollectorRegistry()
        self.requests = Counter(
            "http_requests_total",
            "Anzahl HTTP-Requests",
            ["method", "path", "status"],
            registry=self.registry,
        )
        self.latency = Histogram(
            "http_request_duration_seconds",
            "Dauer der HTTP-Requests in Sekunden",
            ["method", "path"],
            buckets=self.DEFAULT_BUCKETS,
            registry=self.registry,
        )
        self.in_progress = Counter(
            "http_requests_exceptions_total",
            "HTTP-Requests, die mit einer Exception endeten",
            ["method", "path"],
            registry=self.registry,
        )

    def observe(self, method: str, path: str, status: int, duration_s: float) -> None:
        self.requests.labels(method, path, str(status)).inc()
        self.latency.labels(method, path).observe(duration_s)

    def observe_exception(self, method: str, path: str) -> None:
        self.in_progress.labels(method, path).inc()

    def render(self) -> bytes:
        return generate_latest(self.registry)


def normalize_path(raw: str, known: frozenset[str] | None = None) -> str:
    """Reduziert die Pfad-Kardinalität (Prometheus-Label-Explosion vermeiden).

    Bekannte Routen bleiben erhalten; alles andere wird zu `/other`. So sprengen
    dynamische Segmente (IDs) die Metrik nicht.
    """
    path = raw.split("?", 1)[0]
    if known is None:
        return path
    return path if path in known else "/other"


def make_metrics_middleware(
    metrics: HttpMetrics,
    known_paths: frozenset[str] | None = None,
    clock: Callable[[], float] = time.perf_counter,
):
    """Baut eine Starlette/FastAPI-`http`-Middleware, die jeden Request misst."""

    async def middleware(request, call_next: Callable[[object], Awaitable[object]]):
        method = request.method
        path = normalize_path(request.url.path, known_paths)
        start = clock()
        try:
            response = await call_next(request)
        except Exception:
            metrics.observe_exception(method, path)
            raise
        duration = clock() - start
        metrics.observe(method, path, response.status_code, duration)
        return response

    return middleware
