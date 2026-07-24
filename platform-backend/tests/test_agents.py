"""Tests der Agenten-Schicht — Kontroll-Logik ohne echtes Modell."""

import pytest

from app.agents.approval import ApprovalQueue, ApprovalStatus
from app.agents.orchestrator import Orchestrator, OrchestratorLimits, OrchestratorStatus
from app.agents.runtime import AgentContext, AgentRuntime, RunState, RunStatus
from app.agents.spec import AgentSpec, Limits
from app.agents.tools import RiskClass, Tool, ToolRegistry
from app.models.cache import TenantBudget


# ---------------- Werkzeuge & Risiko ----------------
def test_tool_risiko_und_freigabepflicht():
    read = Tool("suche", RiskClass.READ, lambda a: "x")
    mail = Tool("mail_senden", RiskClass.EXTERNAL, lambda a: "gesendet")
    assert read.requires_approval() is False
    assert mail.requires_approval() is True
    reg = ToolRegistry()
    reg.register(read); reg.register(mail)
    assert reg.requires_approval("mail_senden") is True
    with pytest.raises(ValueError):
        reg.register(read)  # doppelte Registrierung


# ---------------- Genehmigungs-Queue + Isolation ----------------
def test_approval_isolation():
    q = ApprovalQueue()
    r = q.submit("t-a", "run1", "mail_senden", {"to": "x"})
    assert q.pending("t-a") == [r]
    assert q.get("t-b", r.id) is None            # fremder Tenant sieht nichts
    with pytest.raises(KeyError):
        q.approve("t-b", r.id, "boese")          # fremder Tenant darf nicht entscheiden
    q.approve("t-a", r.id, "chef")
    assert r.status is ApprovalStatus.APPROVED
    with pytest.raises(ValueError):
        q.approve("t-a", r.id, "chef")           # nicht zweimal


# ---------------- Runtime-Fixtures ----------------
def _scripted(decisions):
    it = iter(decisions)
    def llm(state):
        try:
            return next(it)
        except StopIteration:
            return {"action": "final", "content": "fertig", "tokens": 1}
    return llm


def _ctx(decisions, allowed=("suche", "mail_senden"), limits=None, budget=None):
    reg = ToolRegistry()
    reg.register(Tool("suche", RiskClass.READ, lambda a: "treffer"))
    reg.register(Tool("mail_senden", RiskClass.EXTERNAL, lambda a: "gesendet"))
    spec = AgentSpec("support", "Kundensupport", frozenset(allowed), limits or Limits())
    return AgentContext(spec, reg, ApprovalQueue(),
                        budget or TenantBudget(1_000_000), _scripted(decisions))


# ---------------- Runtime-Verhalten ----------------
def test_final_beendet_lauf():
    ctx = _ctx([{"action": "final", "content": "antwort", "tokens": 3}])
    s = AgentRuntime().run(ctx, "r1", "t1", "ziel")
    assert s.status is RunStatus.DONE and s.result == "antwort"


def test_sicheres_werkzeug_wird_ausgefuehrt():
    ctx = _ctx([{"action": "tool", "tool": "suche", "args": {"q": "x"}, "tokens": 2},
                {"action": "final", "content": "ok", "tokens": 1}])
    s = AgentRuntime().run(ctx, "r1", "t1", "ziel")
    assert s.status is RunStatus.DONE
    assert any(e["kind"] == "tool_result" and e.get("result") == "treffer" for e in s.history)


def test_riskantes_werkzeug_pausiert_fuer_freigabe():
    ctx = _ctx([{"action": "tool", "tool": "mail_senden", "args": {"to": "a"}, "tokens": 2},
                {"action": "final", "content": "gesendet-ok", "tokens": 1}])
    rt = AgentRuntime()
    s = rt.run(ctx, "r1", "t1", "ziel")
    assert s.status is RunStatus.WAITING_APPROVAL
    assert s.pending and s.pending["tool"] == "mail_senden"
    # Mail wurde NICHT ausgeführt
    assert not any(e["kind"] == "tool_result" for e in s.history)
    assert len(ctx.approval.pending("t1")) == 1

    # Freigabe -> ausführen + weiter -> fertig
    s2 = rt.resume(ctx, s, approved=True, by="chef")
    assert s2.status is RunStatus.DONE
    assert any(e["kind"] == "tool_result" and e["tool"] == "mail_senden" for e in s2.history)


def test_ablehnung_fuehrt_werkzeug_nicht_aus():
    ctx = _ctx([{"action": "tool", "tool": "mail_senden", "args": {}, "tokens": 1},
                {"action": "final", "content": "anders geloest", "tokens": 1}])
    rt = AgentRuntime()
    s = rt.run(ctx, "r1", "t1", "ziel")
    s2 = rt.resume(ctx, s, approved=False, by="chef")
    assert s2.status is RunStatus.DONE
    assert any(e["kind"] == "tool_rejected" for e in s2.history)
    assert not any(e["kind"] == "tool_result" for e in s2.history)


def test_max_steps_greift():
    decs = [{"action": "tool", "tool": "suche", "args": {}, "tokens": 1} for _ in range(10)]
    ctx = _ctx(decs, limits=Limits(max_steps=2))
    s = AgentRuntime().run(ctx, "r1", "t1", "ziel")
    assert s.status is RunStatus.MAX_STEPS
    assert s.steps == 2


def test_budget_pro_lauf_greift():
    ctx = _ctx([{"action": "tool", "tool": "suche", "args": {}, "tokens": 5}] * 5,
               limits=Limits(max_tokens_per_run=8))
    s = AgentRuntime().run(ctx, "r1", "t1", "ziel")
    assert s.status is RunStatus.BUDGET_EXCEEDED


def test_tages_budget_pro_tenant_greift():
    ctx = _ctx([{"action": "tool", "tool": "suche", "args": {}, "tokens": 5}] * 5,
               budget=TenantBudget(daily_limit_tokens=7))
    s = AgentRuntime().run(ctx, "r1", "t1", "ziel")
    assert s.status is RunStatus.BUDGET_EXCEEDED


def test_nicht_erlaubtes_werkzeug_wird_verweigert():
    ctx = _ctx([{"action": "tool", "tool": "mail_senden", "args": {}, "tokens": 1}],
               allowed=("suche",))  # mail nicht erlaubt
    s = AgentRuntime().run(ctx, "r1", "t1", "ziel")
    assert s.status is RunStatus.TOOL_ERROR


def test_runstate_serialisierung_roundtrip():
    ctx = _ctx([{"action": "final", "content": "x", "tokens": 1}])
    s = AgentRuntime().run(ctx, "r1", "t1", "ziel")
    again = RunState.from_dict(s.to_dict())
    assert again.status is s.status and again.result == s.result and again.history == s.history


# ---------------- Orchestrator ----------------
def _worker_ctx():
    reg = ToolRegistry()
    spec = AgentSpec("worker", "Allrounder", frozenset(), Limits())
    # Worker finalisiert sofort mit einem Ergebnis, das die Teilaufgabe nennt.
    llm = lambda state: {"action": "final", "content": f"res:{state.goal}", "tokens": 1}
    return AgentContext(spec, reg, ApprovalQueue(), TenantBudget(1_000_000), llm)


def test_orchestrator_zerlegt_prueft_synthetisiert():
    orch = Orchestrator(
        AgentRuntime(), _worker_ctx(),
        planner=lambda g: ["teil-a", "teil-b"],
        verifier=lambda g, r: {"ok": True, "reason": "gut"},
        synthesizer=lambda g, r: " | ".join(r),
    )
    out = orch.run("t1", "grosses ziel")
    assert out.status is OrchestratorStatus.DONE
    assert out.final == "res:teil-a | res:teil-b"
    assert out.attempts == 1


def test_orchestrator_eskaliert_wenn_pruefung_scheitert():
    orch = Orchestrator(
        AgentRuntime(), _worker_ctx(),
        planner=lambda g: ["x"],
        verifier=lambda g, r: {"ok": False, "reason": "zu duenn"},
        synthesizer=lambda g, r: "ignored",
        limits=OrchestratorLimits(max_retries=1),
    )
    out = orch.run("t1", "ziel")
    assert out.status is OrchestratorStatus.ESCALATED
    assert out.attempts == 2               # Erstversuch + 1 Wiederholung
    assert out.escalation_reason == "zu duenn"


def test_orchestrator_tiefenlimit_bearbeitet_direkt():
    orch = Orchestrator(
        AgentRuntime(), _worker_ctx(),
        planner=lambda g: ["sollte-nicht-genutzt-werden"],
        verifier=lambda g, r: {"ok": True, "reason": ""},
        synthesizer=lambda g, r: "x",
        limits=OrchestratorLimits(max_depth=0),
    )
    out = orch.run("t1", "ziel", depth=0)
    assert out.status is OrchestratorStatus.DONE
    assert out.subtasks == ["ziel"]        # nicht zerlegt
    assert out.final == "res:ziel"
