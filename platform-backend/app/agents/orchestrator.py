"""Orchestrator (Auftrag §6): Zerlegung, Delegation, Prüfung, Wiederholung, Eskalation.

Zerlegt ein Ziel in Teilaufgaben, delegiert jede an einen Worker-Agenten
(AgentRuntime), lässt das Gesamtergebnis von einem Prüfer bewerten und wiederholt
bei Bedarf. Harte Grenzen: max. Teilaufgaben, max. Wiederholungen, max. Tiefe —
danach Eskalation an den Menschen statt Endlosschleife.

Planer/Prüfer/Synthese sind injizierbar → ohne echtes Modell testbar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from .runtime import AgentContext, AgentRuntime, RunState, RunStatus


class OrchestratorStatus(str, Enum):
    DONE = "done"
    ESCALATED = "escalated"


#: goal -> Teilaufgaben
Planner = Callable[[str], list[str]]
#: (goal, subtask_results) -> {"ok": bool, "reason": str}
Verifier = Callable[[str, list[str]], dict]
#: (goal, subtask_results) -> Endergebnis
Synthesizer = Callable[[str, list[str]], str]


@dataclass(frozen=True)
class OrchestratorLimits:
    max_subtasks: int = 6
    max_retries: int = 1
    max_depth: int = 3


@dataclass
class OrchestratorResult:
    status: OrchestratorStatus
    goal: str
    final: str | None
    subtasks: list[str] = field(default_factory=list)
    subtask_results: list[str] = field(default_factory=list)
    attempts: int = 0
    verification: dict | None = None
    escalation_reason: str | None = None

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["status"] = self.status.value
        return d


class Orchestrator:
    def __init__(self, runtime: AgentRuntime, worker_ctx: AgentContext,
                 planner: Planner, verifier: Verifier, synthesizer: Synthesizer,
                 limits: OrchestratorLimits | None = None) -> None:
        self._runtime = runtime
        self._worker = worker_ctx
        self._planner = planner
        self._verifier = verifier
        self._synth = synthesizer
        self._limits = limits or OrchestratorLimits()

    def run(self, tenant: str, goal: str, depth: int = 0) -> OrchestratorResult:
        if not tenant:
            raise ValueError("Orchestrator verlangt einen tenant")

        # Tiefe erschöpft → nicht weiter zerlegen, Ziel direkt bearbeiten.
        if depth >= self._limits.max_depth:
            state = self._run_worker(tenant, goal, depth)
            final = state.result if state.status is RunStatus.DONE else None
            status = OrchestratorStatus.DONE if final else OrchestratorStatus.ESCALATED
            return OrchestratorResult(
                status=status, goal=goal, final=final, subtasks=[goal],
                subtask_results=[final or ""], attempts=1,
                escalation_reason=None if final else f"Worker endete mit {state.status.value}",
            )

        subtasks = list(self._planner(goal))[: self._limits.max_subtasks]
        if not subtasks:
            subtasks = [goal]

        attempts = 0
        results: list[str] = []
        verification: dict = {"ok": False, "reason": "nicht ausgeführt"}

        while attempts <= self._limits.max_retries:
            attempts += 1
            results = []
            for sub in subtasks:
                state = self._run_worker(tenant, sub, depth)
                results.append(state.result or "")
            verification = self._verifier(goal, results)
            if verification.get("ok"):
                break

        if not verification.get("ok"):
            return OrchestratorResult(
                status=OrchestratorStatus.ESCALATED, goal=goal, final=None,
                subtasks=subtasks, subtask_results=results, attempts=attempts,
                verification=verification,
                escalation_reason=verification.get("reason", "Prüfung fehlgeschlagen"),
            )

        final = self._synth(goal, results)
        return OrchestratorResult(
            status=OrchestratorStatus.DONE, goal=goal, final=final,
            subtasks=subtasks, subtask_results=results, attempts=attempts,
            verification=verification,
        )

    def _run_worker(self, tenant: str, subtask: str, depth: int) -> RunState:
        run_id = f"{tenant}:{depth}:{abs(hash(subtask)) % 10_000_000}"
        return self._runtime.run(self._worker, run_id, tenant, subtask)
