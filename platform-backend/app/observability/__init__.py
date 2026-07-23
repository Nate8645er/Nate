"""observability/ — OpenTelemetry ab Tag 1 (Auftrag §8/§B.9).

No-op, solange kein OTEL-Exporter konfiguriert ist (honest not-configured):
Instrumentierung existiert im Code, kostet aber nichts, bis ein Collector da ist.
"""

from __future__ import annotations

import os


def otel_configured(env: dict[str, str] | None = None) -> bool:
    e = env if env is not None else dict(os.environ)
    return bool((e.get("OTEL_EXPORTER_OTLP_ENDPOINT") or "").strip())


def setup_tracing(service_name: str = "platform-backend", env: dict[str, str] | None = None) -> bool:
    """Richtet Tracing ein, wenn ein OTLP-Endpoint gesetzt ist. Gibt zurück, ob aktiv."""
    if not otel_configured(env):
        return False
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider

        provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
        trace.set_tracer_provider(provider)
        return True
    except ImportError:
        return False
