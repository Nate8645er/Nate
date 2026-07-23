"""Agent-Runtime (Auftrag §6).

Führt einen Agenten schrittweise aus. Der Zustand (`RunState`) ist vollständig
serialisierbar → er lebt in der DB, nicht im Prozess; jeder Worker kann jederzeit
neu starten und weitermachen. Harte Grenzen (Schritte, Budget) werden erzwungen.
Riskante Werkzeuge pausieren den Lauf, bis eine Freigabe vorliegt.

Das LLM ist injizierbar: eine Funktion `RunState -> Decision`. Dadurch ist die
gesamte Kontroll-Logik ohne echtes Modell testbar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from .approval import ApprovalQueue
from .spec import AgentSpec
from .tools import ToolRegistry
from ..models.cache import TenantBudget


class RunStatus(str, Enum):
    RUNNING = "running"
    DONE = "done"
    WAITING_APPROVAL = "waiting_approval"
    MAX_STEPS = "max_steps"
    BUDGET_EXCEEDED = "budget_exceeded"
    TOOL_ERROR = "tool_error"


@dataclass
class RunState:
    run_id: str
    tenant: str
    goal: str
    status: RunStatus = RunStatus.RUNNING
    steps: int = 0
    spent_tokens: int = 0
    result: str | None = None
    history: list[dict] = field(default_factory=list)
    pending: dict | None = None  # {"request_id","tool","args"} während Freigabe

    def event(self, kind: str, data: dict) -> None:
        self.history.append({"step": self.steps, "kind": kind, **data})

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["status"] = self.status.value
        return d

    @staticmethod
    def from_dict(d: dict) -> "RunState":
        d = dict(d)
        d["status"] = RunStatus(d["status"])
        return RunState(**d)


#: Entscheidung des Modells: {"action":"tool","tool":..,"args":..} oder
#: {"action":"final","content":..}. Optional "tokens", "reason".
Decision = dict
LLM = Callable[[RunState], Decision]


@dataclass
class AgentContext:
    spec: AgentSpec
    tools: ToolRegistry
    approval: ApprovalQueue
    budget: TenantBudget
    llm: LLM


class AgentRuntime:
    def run(self, ctx: AgentContext, run_id: str, tenant: str, goal: str) -> RunState:
        state = RunState(run_id=run_id, tenant=tenant, goal=goal)
        return self._drive(ctx, state)

    def resume(self, ctx: AgentContext, state: RunState, approved: bool, by: str = "mensch") -> RunState:
        if state.status is not RunStatus.WAITING_APPROVAL or not state.pending:
            raise ValueError("resume nur im Zustand waiting_approval mit offener Freigabe")
        req_id = state.pending["request_id"]
        tool_name = state.pending["tool"]
        args = state.pending["args"]
        if approved:
            ctx.approval.approve(state.tenant, req_id, by)
            tool = ctx.tools.get(tool_name)
            self._execute(state, tool, args)
        else:
            ctx.approval.reject(state.tenant, req_id, by)
            state.event("tool_rejected", {"tool": tool_name})
        state.pending = None
        state.status = RunStatus.RUNNING
        return self._drive(ctx, state)

    # -------------------------------------------------------------- #
    def _drive(self, ctx: AgentContext, state: RunState) -> RunState:
        limits = ctx.spec.limits
        while state.status is RunStatus.RUNNING:
            if state.steps >= limits.max_steps:
                state.status = RunStatus.MAX_STEPS
                break
            decision = ctx.llm(state)
            tokens = int(decision.get("tokens", 1))
            # Budget: pro Lauf UND pro Tag/Tenant
            if state.spent_tokens + tokens > limits.max_tokens_per_run or not ctx.budget.allow(state.tenant, tokens):
                state.status = RunStatus.BUDGET_EXCEEDED
                state.event("budget_stop", {"spent": state.spent_tokens})
                break
            ctx.budget.charge(state.tenant, tokens)
            state.spent_tokens += tokens

            action = decision.get("action")
            if action == "final":
                state.result = str(decision.get("content", ""))
                state.status = RunStatus.DONE
                state.event("final", {})
                break
            if action == "tool":
                self._handle_tool(ctx, state, decision)
                continue
            state.event("unknown_action", {"action": action})
            state.status = RunStatus.TOOL_ERROR
            break
        return state

    def _handle_tool(self, ctx: AgentContext, state: RunState, decision: Decision) -> None:
        name = decision.get("tool", "")
        args = decision.get("args", {}) or {}
        tool = ctx.tools.get(name)
        if tool is None or name not in ctx.spec.allowed_tools:
            state.event("tool_denied", {"tool": name})
            state.status = RunStatus.TOOL_ERROR
            return
        if tool.requires_approval():
            req = ctx.approval.submit(state.tenant, state.run_id, name, args,
                                      reason=decision.get("reason", ""))
            state.pending = {"request_id": req.id, "tool": name, "args": args}
            state.status = RunStatus.WAITING_APPROVAL
            state.event("approval_needed", {"tool": name, "request_id": req.id})
            return
        self._execute(state, tool, args)

    def _execute(self, state: RunState, tool, args: dict) -> None:
        try:
            result = tool.execute(args)
            state.event("tool_result", {"tool": tool.name, "result": result})
        except Exception as exc:  # noqa: BLE001 — Werkzeugfehler abfangen, nicht crashen
            state.event("tool_error", {"tool": tool.name, "error": str(exc)})
        state.steps += 1
