"""FastAPI-Einstiegspunkt des platform-backend.

Nur Fundament (Phase 1): Health-/Erkennungs-Endpunkte, die ehrlich melden, was
konfiguriert bzw. an Hardware vorhanden ist. Fachliche Endpunkte kommen ab
Phase 2. Läuft vollständig OHNE GPU und OHNE konfigurierte Dienste.
"""

from __future__ import annotations

from fastapi import FastAPI

from . import __version__
from .compute.hal import detect_summary
from .config import get_settings

app = FastAPI(
    title="KI-System · platform-backend",
    version=__version__,
    description="Additive Enterprise-Schicht (Compute-HAL, Modell-Router, Agenten, Automation).",
)


@app.get("/health")
def health() -> dict:
    """Lebt der Dienst? Plus ehrlicher Konfigurationsstatus (ohne Secrets)."""
    return {
        "status": "ok",
        "version": __version__,
        "env": get_settings().env_name,
        "services": get_settings().snapshot(),
    }


@app.get("/health/compute")
def health_compute() -> dict:
    """Welche Recheneinheiten sind vorhanden? CPU immer, GPU falls erkannt."""
    return detect_summary()
