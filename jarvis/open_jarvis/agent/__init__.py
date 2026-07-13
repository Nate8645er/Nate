"""JARVIS-Agent — agentische Befehlsausfuehrung (Plan -> Werkzeuge -> Ergebnis).

Gibt JARVIS die Faehigkeit, gesprochene/getippte Befehle wirklich auszufuehren,
mit auswaehlbarem KI-Motor (inkl. Fable 5) und echten Werkzeugen wie dem
Shop-Bauplan-Generator.

Beispiel:

    from open_jarvis.agent import JarvisAgent
    run = JarvisAgent(model="fable-5", execute=True).run("baue einen Shop fuer Kaffee")
    print(run.plan.final)
"""

from __future__ import annotations

from open_jarvis.agent.agent import AgentRun, JarvisAgent, StepOutcome, render_run
from open_jarvis.agent.models import (
    AgentModel,
    default_model,
    list_models,
    resolve_model,
)
from open_jarvis.agent.tools import Tool, ToolContext, ToolResult, build_default_registry

__all__ = [
    "AgentModel",
    "AgentRun",
    "JarvisAgent",
    "StepOutcome",
    "Tool",
    "ToolContext",
    "ToolResult",
    "build_default_registry",
    "default_model",
    "list_models",
    "render_run",
    "resolve_model",
]
