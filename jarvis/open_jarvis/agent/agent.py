"""JARVIS-Agent: nimmt einen Befehl entgegen und fuehrt ihn aus.

Der Ablauf entspricht dem Prinzip von Claude Code:

    Befehl -> Planen (Modell/lokal) -> Werkzeuge ausfuehren -> Ergebnis berichten

Standardmodell ist **Fable 5**; ohne API-Schluessel arbeitet der Agent
automatisch lokal weiter. Datei-/Shop-Werkzeuge wirken nur im ``execute=True``-
Modus echt; sonst laeuft eine gefahrlose Vorschau (Trockenlauf).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from open_jarvis.agent.models import AgentModel, resolve_model
from open_jarvis.agent.planner import Plan, build_planner
from open_jarvis.agent.tools import Tool, ToolContext, ToolResult, build_default_registry

DEFAULT_WORKSPACE = Path.home() / ".jarvis" / "agent_workspace"


@dataclass
class StepOutcome:
    tool: str
    args: dict[str, Any]
    why: str
    result: ToolResult

    def to_dict(self) -> dict[str, Any]:
        return {"tool": self.tool, "args": self.args, "why": self.why, "result": self.result.to_dict()}


@dataclass
class AgentRun:
    task: str
    model: str
    planner: str
    plan: Plan
    outcomes: list[StepOutcome] = field(default_factory=list)
    execute: bool = False

    @property
    def ok(self) -> bool:
        return all(outcome.result.ok for outcome in self.outcomes) if self.outcomes else True

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "model": self.model,
            "planner": self.planner,
            "execute": self.execute,
            "note": self.plan.note,
            "final": self.plan.final,
            "steps": [outcome.to_dict() for outcome in self.outcomes],
            "ok": self.ok,
        }


class JarvisAgent:
    """Agent, der Befehle plant und mit echten Werkzeugen ausfuehrt."""

    def __init__(
        self,
        *,
        model: AgentModel | str | None = None,
        workspace: Path | str | None = None,
        registry: dict[str, Tool] | None = None,
        execute: bool = False,
    ) -> None:
        self.model = model if isinstance(model, AgentModel) else resolve_model(model)
        self.workspace = Path(workspace) if workspace else DEFAULT_WORKSPACE
        self.registry = registry if registry is not None else build_default_registry()
        self.execute = execute
        self.planner = build_planner(self.model)

    def run(self, task: str) -> AgentRun:
        plan = self.planner.plan(task, self.registry)
        run = AgentRun(task=task, model=self.model.key, planner=plan.planner, plan=plan, execute=self.execute)
        ctx = ToolContext(workspace=self.workspace, execute=self.execute)
        for step in plan.steps:
            tool_name = step.get("tool", "")
            args = step.get("args", {}) if isinstance(step.get("args"), dict) else {}
            why = str(step.get("why", ""))
            tool = self.registry.get(tool_name)
            if tool is None:
                result = ToolResult(False, f"Unbekanntes Werkzeug: {tool_name}")
            else:
                try:
                    result = tool.handler(args, ctx)
                except Exception as exc:  # Werkzeug-Fehler duerfen den Lauf nicht killen.
                    result = ToolResult(False, f"Fehler in '{tool_name}': {exc}")
            run.outcomes.append(StepOutcome(tool=tool_name, args=args, why=why, result=result))
        return run


def render_run(run: AgentRun) -> str:
    """Menschlich lesbarer Bericht eines Agentenlaufs (Deutsch)."""

    lines = [
        f"🤖 JARVIS-Agent · Modell: {run.model} · Modus: {'AUSFUEHREN' if run.execute else 'Vorschau'}",
        f"📋 Aufgabe: {run.task}",
    ]
    if run.plan.note:
        lines.append(f"ℹ️  {run.plan.note}")
    lines.append("")
    for index, outcome in enumerate(run.outcomes, start=1):
        icon = "✅" if outcome.result.ok else "❌"
        lines.append(f"{icon} Schritt {index}: {outcome.tool} — {outcome.result.summary}")
        if outcome.why:
            lines.append(f"     ↳ {outcome.why}")
        path = outcome.result.data.get("path")
        url = outcome.result.data.get("url")
        if path:
            lines.append(f"     📁 {path}")
        if url:
            lines.append(f"     🔗 {url}")
    lines.append("")
    lines.append(f"🏁 {run.plan.final}")
    return "\n".join(lines)
