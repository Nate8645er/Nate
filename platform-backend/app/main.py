"""FastAPI-Einstiegspunkt des platform-backend.

Fundament + Hardening (Phase 8): ehrliche Health-/Erkennungs-Endpunkte plus
Observability (Prometheus `/metrics`, HTTP-Latenz-Middleware, OTEL-Tracing wenn
konfiguriert) und Kubernetes-taugliche Liveness/Readiness. Läuft vollständig
OHNE GPU und OHNE konfigurierte Dienste (dann melden Endpunkte das ehrlich).
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response

from . import __version__
from .api.v1 import router as api_v1_router
from .compute.hal import sample_device_metrics
from .compute.metrics import render_metrics
from .config import get_settings
from .observability import setup_tracing
from .observability.http_metrics import HttpMetrics, make_metrics_middleware
from .observability.readiness import evaluate_readiness


def _wire_vector_store() -> None:
    """Verbindet die Wissens-API mit dem echten Qdrant, wenn konfiguriert.

    Ehrlich: Ist QDRANT_URL nicht gesetzt oder Qdrant nicht erreichbar, bleibt
    der Store None → /knowledge/* meldet 503 (kein Schein-Betrieb).
    """
    settings = get_settings()
    if not settings.qdrant.configured:
        return
    try:
        from qdrant_client import QdrantClient

        from .api import v1
        from .knowledge.vectorstore import QdrantVectorStore

        client = QdrantClient(url=settings.qdrant.url)
        store = QdrantVectorStore(client, collection="knowledge", dim=v1._embedder.dim)
        v1.set_vector_store(store)
    except Exception:  # noqa: BLE001 — Wiring darf den Start nie verhindern
        pass


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # OTEL-Tracing nur, wenn ein OTLP-Endpoint gesetzt ist (sonst no-op).
    setup_tracing(env=dict(os.environ))
    # Wissens-API mit echtem Qdrant verbinden, falls konfiguriert.
    _wire_vector_store()
    yield


app = FastAPI(
    title="KI-System · platform-backend",
    version=__version__,
    description="Additive Enterprise-Schicht (Compute-HAL, Modell-Router, Agenten, Automation).",
    lifespan=lifespan,
)

# Observability: eigene Registry für App-Metriken; Middleware misst jeden Request.
_http_metrics = HttpMetrics()
#: Bekannte Routen — begrenzt die Label-Kardinalität (keine ID-Explosion).
_KNOWN_PATHS = frozenset(
    {"/health", "/health/compute", "/health/live", "/health/ready", "/metrics", "/"}
)
app.middleware("http")(make_metrics_middleware(_http_metrics, known_paths=_KNOWN_PATHS))

# HTTP-API v1 (Cutover-Fundament) — additiv zu den Health-/Metrics-Endpunkten.
app.include_router(api_v1_router)


@app.get("/health")
def health() -> dict:
    """Lebt der Dienst? Plus ehrlicher Konfigurationsstatus (ohne Secrets)."""
    return {
        "status": "ok",
        "version": __version__,
        "env": get_settings().env_name,
        "services": get_settings().snapshot(),
    }


@app.get("/health/live")
def health_live() -> dict:
    """Liveness: billig, ohne externe Aufrufe. Nur: läuft der Prozess?"""
    return {"status": "alive", "version": __version__}


@app.get("/health/ready")
def health_ready(response: Response) -> dict:
    """Readiness: konfigurierte Abhängigkeiten müssen erreichbar sein.

    Ohne injizierte Netz-Proben gelten konfigurierte Dienste als
    „konfiguriert (ungeprüft)"; nicht konfigurierte als „übersprungen". Nur ein
    konfigurierter + geprüft-nicht-erreichbarer Dienst macht `ready=false`
    (HTTP 503) — dann nimmt k8s die Instanz aus dem Load-Balancer.
    """
    report = evaluate_readiness()
    if not report.ready:
        response.status_code = 503
    return report.to_dict()


@app.get("/health/compute")
def health_compute() -> dict:
    """Welche Recheneinheiten sind vorhanden? CPU immer, GPU falls erkannt."""
    from .compute.hal import detect_summary

    return detect_summary()


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus-Endpunkt: HTTP-App-Metriken + Compute-Gauges (Momentaufnahme)."""
    body = _http_metrics.render()
    # Compute-Gauges anhängen (aktuelle Geräte-Metriken, falls erkennbar).
    try:
        body += render_metrics(sample_device_metrics())
    except Exception:  # noqa: BLE001 — Metriken dürfen den Endpunkt nie brechen
        pass
    return Response(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")
