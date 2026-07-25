"""Metriken im Prometheus-Format (Phase 7, Monitoring).

Bewusst schlank: Request-Zaehler/-Latenz pro Route+Status (universell
nuetzlich fuer jedes Grafana-Dashboard), plus die zwei fachlichen Zahlen,
die im Betrieb am ehesten gebraucht werden — Chat-Aufrufe und verbrauchte
Tokens, beide nach Modell aufgeschluesselt.
"""
from __future__ import annotations

import time

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

http_requests_total = Counter(
    "http_requests_total",
    "Anzahl HTTP-Requests",
    ["method", "route", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "Dauer von HTTP-Requests in Sekunden",
    ["method", "route"],
)

chat_completions_total = Counter(
    "chat_completions_total",
    "Anzahl abgeschlossener Chat-Aufrufe (Route /v1/chat, /v1/agents/*/chat)",
    ["model"],
)

chat_tokens_total = Counter(
    "chat_tokens_total",
    "Verbrauchte Tokens ueber alle Mandanten",
    ["model", "direction"],  # direction: in | out
)


def _route_label(request: Request) -> str:
    """Nutzt die geroutete Pfad-Vorlage (z.B. '/v1/agents/{agent_id}') statt
    des echten Pfads, damit dynamische IDs die Kardinalitaet nicht sprengen."""
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        route = _route_label(request)
        http_requests_total.labels(request.method, route, str(response.status_code)).inc()
        http_request_duration_seconds.labels(request.method, route).observe(duration)
        return response


def record_chat_usage(model: str, tokens_in: int, tokens_out: int) -> None:
    chat_completions_total.labels(model).inc()
    chat_tokens_total.labels(model, "in").inc(tokens_in)
    chat_tokens_total.labels(model, "out").inc(tokens_out)
