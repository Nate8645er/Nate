"""ModelRouter — Routing-Policy (rein) + Ausführung (LiteLLM-Adapter).

Auftrag §5.4: Entscheidung anhand von
  Datenklassifikation (local_only bindend) → benötigte Fähigkeit → Latenzziel →
  Kosten → Auslastung; Fallback-Kette mit Circuit-Breaker; jede Entscheidung
  wird mit Begründung geloggt.

Diese Datei enthält die reine Entscheidungslogik + einen dünnen Ausführungs-
Adapter. LiteLLM wird NUR beim tatsächlichen Aufruf importiert, damit die
Policy ohne installiertes LiteLLM getestet werden kann.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class DataClass(str, Enum):
    """Datenklassifikation des Tenants. `LOCAL_ONLY` ist bindend."""

    LOCAL_ONLY = "local_only"
    INTERNAL = "internal"
    PUBLIC = "public"


Placement = Literal["local", "cloud"]


@dataclass(frozen=True)
class ModelRequest:
    prompt_tokens_est: int
    data_class: DataClass = DataClass.INTERNAL
    #: Fähigkeiten, die das Modell können muss (z. B. {"vision"}).
    needs: frozenset[str] = field(default_factory=frozenset)
    latency_target_ms: int | None = None
    #: Bevorzugtes Modell (optional); leer = Router wählt.
    model: str | None = None


@dataclass(frozen=True)
class RoutingContext:
    """Momentaufnahme der Umgebung für die Entscheidung."""

    local_available: bool
    local_capabilities: frozenset[str] = field(default_factory=frozenset)
    cloud_available: bool = True
    local_load_pct: float = 0.0
    #: ab dieser lokalen Auslastung wird trotz Präferenz in die Cloud ausgewichen
    local_load_ceiling_pct: float = 85.0


@dataclass(frozen=True)
class RoutingDecision:
    placement: Placement
    reason: str
    fallback: Placement | None


def decide(req: ModelRequest, ctx: RoutingContext) -> RoutingDecision:
    """Reine Routing-Entscheidung mit Begründung. Kein Netz, kein Import."""
    # 1) Datenklassifikation ist bindend.
    if req.data_class is DataClass.LOCAL_ONLY:
        if not ctx.local_available:
            return RoutingDecision("local", "local_only erzwingt lokal – aber kein lokales Backend verfügbar", None)
        if req.needs and not req.needs <= ctx.local_capabilities:
            fehlend = ", ".join(sorted(req.needs - ctx.local_capabilities))
            return RoutingDecision("local", f"local_only bindend, aber Fähigkeit fehlt lokal: {fehlend}", None)
        return RoutingDecision("local", "local_only: Daten dürfen die Umgebung nicht verlassen", None)

    # 2) Fähigkeit lokal nicht verfügbar → Cloud (falls möglich).
    if req.needs and not req.needs <= ctx.local_capabilities:
        if ctx.cloud_available:
            return RoutingDecision("cloud", "benötigte Fähigkeit lokal nicht verfügbar", "local")
        return RoutingDecision("local", "Fähigkeit fehlt lokal, aber keine Cloud verfügbar – Best Effort lokal", None)

    # 3) Lokal bevorzugt, wenn verfügbar und nicht überlastet.
    if ctx.local_available and ctx.local_load_pct < ctx.local_load_ceiling_pct:
        return RoutingDecision("local", "lokales Backend verfügbar und nicht überlastet (Kosten/Datenhoheit)", "cloud" if ctx.cloud_available else None)

    # 4) Sonst Cloud.
    if ctx.cloud_available:
        grund = "lokal überlastet" if ctx.local_available else "kein lokales Backend"
        return RoutingDecision("cloud", grund, "local" if ctx.local_available else None)

    # 5) Nichts verfügbar.
    return RoutingDecision("local", "weder Cloud noch verfügbares lokales Backend – Best Effort", None)


class ModelRouter:
    """Wählt Placement und führt aus (LiteLLM). Ausführung ist optional/lazy."""

    def __init__(self, ctx: RoutingContext, local_base_url: str | None = None) -> None:
        self._ctx = ctx
        self._local_base_url = local_base_url

    def route(self, req: ModelRequest) -> RoutingDecision:
        return decide(req, self._ctx)

    def complete(self, req: ModelRequest, messages: list[dict]) -> dict:
        """Führt die Anfrage gemäß Entscheidung aus. Importiert LiteLLM lazy.

        Gibt bei fehlender Abhängigkeit/Konfiguration ein ehrliches
        `{"ok": False, "error": ...}` zurück statt zu werfen (Muster des
        bestehenden Systems).
        """
        decision = self.route(req)
        try:
            import litellm  # lazy: Policy bleibt ohne LiteLLM testbar
        except ImportError:
            return {"ok": False, "error": "litellm-nicht-installiert", "decision": decision.__dict__}

        kwargs: dict = {"messages": messages}
        if decision.placement == "local":
            if not self._local_base_url:
                return {"ok": False, "error": "lokal gewählt, aber LOCAL_LLM_URL nicht gesetzt", "decision": decision.__dict__}
            kwargs["model"] = "openai/" + (req.model or "local-model")
            kwargs["api_base"] = self._local_base_url
            kwargs["api_key"] = "not-needed"
        else:
            kwargs["model"] = req.model or "gpt-4o-mini"

        try:
            resp = litellm.completion(**kwargs)
            return {"ok": True, "decision": decision.__dict__, "response": resp}
        except Exception as exc:  # noqa: BLE001 — nie werfen an der Schichtgrenze
            return {"ok": False, "error": str(exc), "decision": decision.__dict__}
