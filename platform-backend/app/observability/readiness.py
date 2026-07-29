"""Readiness- & Liveness-Logik (Phase 8 · Hardening).

Kubernetes/k3s unterscheidet:
- **Liveness**: Lebt der Prozess? (billig, kein externer Aufruf) → Neustart bei Fehler.
- **Readiness**: Kann der Dienst Traffic annehmen? → prüft, ob die als
  konfiguriert markierten Abhängigkeiten wirklich erreichbar sind.

Ehrlich (Muster des Systems): Ein Dienst, der NICHT konfiguriert ist, wird als
`skipped` gemeldet, nicht als „gesund" — kein Schein-OK. Nur **konfigurierte**
Abhängigkeiten, die nicht erreichbar sind, machen die App `not ready`.

Die eigentlichen Netz-Prüfungen sind injizierbar (`probes`), damit die Logik
ohne laufende Dienste testbar bleibt.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..config import Settings, get_settings

#: Eine Probe gibt (ok, detail) zurück. Wirft sie, gilt das als nicht erreichbar.
Probe = Callable[[str], tuple[bool, str]]


@dataclass(frozen=True)
class Check:
    name: str
    status: str  # "ok" | "fehler" | "übersprungen"
    detail: str

    @property
    def blocking(self) -> bool:
        return self.status == "fehler"


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    checks: list[Check]

    def to_dict(self) -> dict:
        return {
            "ready": self.ready,
            "checks": [{"name": c.name, "status": c.status, "detail": c.detail} for c in self.checks],
        }


def evaluate_readiness(
    settings: Settings | None = None,
    probes: dict[str, Probe] | None = None,
) -> ReadinessReport:
    """Bewertet die Bereitschaft anhand konfigurierter + erreichbarer Dienste.

    `probes` bildet Dienstname → Probe. Fehlt eine Probe für einen konfigurierten
    Dienst, gilt er als `ok` (konfiguriert, aber ungeprüft) — die Netz-Probe ist
    optional und wird produktiv injiziert.
    """
    s = settings or get_settings()
    probes = probes or {}
    services = {
        "postgres": s.postgres,
        "redis": s.redis,
        "qdrant": s.qdrant,
        "temporal": s.temporal,
        "minio": s.minio,
        "local_llm": s.local_llm,
    }
    checks: list[Check] = []
    for name, cfg in services.items():
        if not cfg.configured:
            checks.append(Check(name, "übersprungen", "nicht konfiguriert"))
            continue
        probe = probes.get(name)
        if probe is None:
            checks.append(Check(name, "ok", "konfiguriert (ungeprüft)"))
            continue
        try:
            ok, detail = probe(cfg.url or "")
        except Exception as exc:  # noqa: BLE001 — Probe-Fehler = nicht erreichbar
            checks.append(Check(name, "fehler", f"nicht erreichbar: {exc}"))
            continue
        checks.append(Check(name, "ok" if ok else "fehler", detail))

    ready = not any(c.blocking for c in checks)
    return ReadinessReport(ready=ready, checks=checks)
