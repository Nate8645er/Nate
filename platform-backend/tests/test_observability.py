"""Tests: Observability (HTTP-Metriken, /metrics, Readiness/Liveness)."""

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.observability.http_metrics import HttpMetrics, normalize_path
from app.observability.readiness import evaluate_readiness

client = TestClient(app)


# --------------------------------------------------------------------------- #
# HttpMetrics
# --------------------------------------------------------------------------- #
def test_normalize_path_begrenzt_kardinalitaet():
    known = frozenset({"/health", "/metrics"})
    assert normalize_path("/health?x=1", known) == "/health"
    assert normalize_path("/tenants/abc-123", known) == "/other"
    assert normalize_path("/beliebig", None) == "/beliebig"  # ohne known: unverändert


def test_httpmetrics_zaehlt_und_rendert():
    m = HttpMetrics()
    m.observe("GET", "/health", 200, 0.012)
    m.observe("GET", "/health", 200, 0.020)
    m.observe("POST", "/other", 500, 0.5)
    text = m.render().decode()
    assert 'http_requests_total{method="GET",path="/health",status="200"} 2.0' in text
    assert "http_request_duration_seconds_bucket" in text


def test_httpmetrics_isolierte_registry():
    # Zwei Instanzen kollidieren nicht (eigene Registry je Instanz).
    a, b = HttpMetrics(), HttpMetrics()
    a.observe("GET", "/x", 200, 0.01)
    assert "/x" in a.render().decode()
    assert "/x" not in b.render().decode()


# --------------------------------------------------------------------------- #
# Readiness
# --------------------------------------------------------------------------- #
def test_readiness_nicht_konfiguriert_ist_bereit():
    # Leere Umgebung: alle Dienste „übersprungen", App ist bereit.
    report = evaluate_readiness(Settings(env={}))
    assert report.ready is True
    assert all(c.status == "übersprungen" for c in report.checks)


def test_readiness_konfiguriert_ohne_probe_ist_ok():
    s = Settings(env={"DATABASE_URL": "postgresql://x/y"})
    report = evaluate_readiness(s)
    pg = next(c for c in report.checks if c.name == "postgres")
    assert pg.status == "ok" and report.ready is True


def test_readiness_konfiguriert_aber_probe_scheitert_blockt():
    s = Settings(env={"DATABASE_URL": "postgresql://x/y"})

    def failing(_url: str):
        raise ConnectionError("refused")

    report = evaluate_readiness(s, probes={"postgres": failing})
    pg = next(c for c in report.checks if c.name == "postgres")
    assert pg.status == "fehler" and pg.blocking is True
    assert report.ready is False


def test_readiness_probe_ok_bleibt_bereit():
    s = Settings(env={"REDIS_URL": "redis://x"})
    report = evaluate_readiness(s, probes={"redis": lambda _u: (True, "pong")})
    assert report.ready is True


# --------------------------------------------------------------------------- #
# Endpunkte (echte ASGI-App via TestClient)
# --------------------------------------------------------------------------- #
def test_liveness_endpunkt():
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"


def test_readiness_endpunkt_200_wenn_bereit():
    r = client.get("/health/ready")
    assert r.status_code == 200
    assert r.json()["ready"] is True


def test_metrics_endpunkt_prometheus_format():
    # Erst einen Request erzeugen, damit der Zähler > 0 ist.
    client.get("/health/live")
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]
    body = r.text
    assert "http_requests_total" in body
    # Compute-Gauge (CPU-RAM) ist angehängt.
    assert "gpu_memory_total_mb" in body


def test_compute_endpunkt_unveraendert():
    r = client.get("/health/compute")
    assert r.status_code == 200
    assert "devices" in r.json()


def test_wire_vector_store_ohne_qdrant_ist_noop():
    # Ohne konfiguriertes Qdrant bleibt der Store None (ehrlich → /knowledge/* 503),
    # der Start darf dabei nie fehlschlagen.
    from app.api import v1
    from app.main import _wire_vector_store

    v1.set_vector_store(None)
    _wire_vector_store()  # QDRANT_URL im Test nicht gesetzt → no-op
    assert v1._vector_store is None
