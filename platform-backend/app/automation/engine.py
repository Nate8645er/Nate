"""Workflow-Engine (Auftrag §Phase 5): durable, wiederaufnehmbar, idempotent.

Interface `WorkflowEngine` + `LocalWorkflowEngine` (in-process). Die lokale
Engine modelliert Temporals Kern-Garantien testbar ohne Server:

* **Durable/wiederaufnehmbar:** jeder Schritt schreibt sein Ergebnis in ein
  Journal (run_id + step). Ein erneuter Lauf mit derselben run_id überspringt
  bereits erledigte Schritte und nutzt deren Ergebnis → nach einem „Absturz"
  wird nahtlos fortgesetzt.
* **Idempotent:** derselbe Schritt läuft nie zweimal; eine Trigger-Auslösung
  mit gleicher idempotency_key wird dedupliziert.
* **Retry mit Backoff:** flüchtige Fehler werden wiederholt, permanente führen
  zu FAILED statt Endlosschleife.

Der Temporal-Adapter (`temporal_adapter.py`) bildet dieselben Begriffe auf das
Temporal-SDK ab, wenn ein Temporal-Server läuft.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Protocol, runtime_checkable


class WorkflowStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 0.5
    factor: float = 2.0

    def backoff(self, attempt: int) -> float:
        """Wartezeit vor Versuch `attempt` (1-basiert)."""
        return self.base_delay * (self.factor ** (attempt - 1))


@runtime_checkable
class Journal(Protocol):
    def get(self, run_id: str, step: str): ...
    def put(self, run_id: str, step: str, result) -> None: ...
    def has(self, run_id: str, step: str) -> bool: ...


class InMemoryJournal:
    def __init__(self) -> None:
        self._data: dict[tuple[str, str], object] = {}

    def get(self, run_id: str, step: str):
        return self._data.get((run_id, step))

    def has(self, run_id: str, step: str) -> bool:
        return (run_id, step) in self._data

    def put(self, run_id: str, step: str, result) -> None:
        self._data[(run_id, step)] = result


@dataclass(frozen=True)
class WorkflowStep:
    name: str
    #: Aktivität: (input, kontext-dict) -> Ergebnis. Wirft bei Fehler.
    fn: Callable[[object, dict], object]
    retry: RetryPolicy = field(default_factory=RetryPolicy)


@dataclass(frozen=True)
class WorkflowDef:
    name: str
    steps: tuple[WorkflowStep, ...]


@dataclass
class WorkflowRun:
    run_id: str
    status: WorkflowStatus
    outputs: dict = field(default_factory=dict)
    failed_step: str | None = None
    error: str | None = None
    attempts: dict = field(default_factory=dict)


class LocalWorkflowEngine:
    def __init__(self, journal: Journal | None = None, sleep: Callable[[float], None] | None = None) -> None:
        self._journal = journal or InMemoryJournal()
        self._sleep = sleep or (lambda _s: None)  # injizierbar für Tests

    def run(self, wf: WorkflowDef, run_id: str, wf_input: object = None) -> WorkflowRun:
        outputs: dict = {}
        attempts: dict = {}
        ctx: dict = {"run_id": run_id, "input": wf_input, "outputs": outputs}

        for step in wf.steps:
            # Wiederaufnahme: erledigter Schritt wird übersprungen (idempotent).
            if self._journal.has(run_id, step.name):
                outputs[step.name] = self._journal.get(run_id, step.name)
                continue

            result, err = self._run_step(step, ctx, attempts)
            if err is not None:
                return WorkflowRun(run_id, WorkflowStatus.FAILED, outputs,
                                   failed_step=step.name, error=err, attempts=attempts)
            self._journal.put(run_id, step.name, result)
            outputs[step.name] = result

        return WorkflowRun(run_id, WorkflowStatus.COMPLETED, outputs, attempts=attempts)

    def _run_step(self, step: WorkflowStep, ctx: dict, attempts: dict):
        last_err = "unbekannt"
        for attempt in range(1, step.retry.max_attempts + 1):
            attempts[step.name] = attempt
            try:
                return step.fn(ctx["input"], ctx), None
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                if attempt < step.retry.max_attempts:
                    # Wartezeit NACH dem soeben fehlgeschlagenen Versuch.
                    self._sleep(step.retry.backoff(attempt))
        return None, last_err
