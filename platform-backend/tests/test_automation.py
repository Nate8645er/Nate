"""Tests: Workflow-Engine, Trigger, Temporal-Adapter — ohne Server/Netz."""


from app.automation.engine import (
    InMemoryJournal,
    LocalWorkflowEngine,
    RetryPolicy,
    WorkflowDef,
    WorkflowStatus,
    WorkflowStep,
)
from app.automation.temporal_adapter import temporal_available, to_temporal_retry
from app.automation.triggers import (
    DailyTrigger,
    EventTrigger,
    IdempotencyGuard,
    IntervalTrigger,
    WebhookTrigger,
)


# ---------------- Engine: Ablauf, Idempotenz, Wiederaufnahme ----------------
def test_workflow_laeuft_schritte_in_reihenfolge():
    steps = (
        WorkflowStep("a", lambda inp, ctx: inp + 1),
        WorkflowStep("b", lambda inp, ctx: ctx["outputs"]["a"] * 10),
    )
    run = LocalWorkflowEngine().run(WorkflowDef("wf", steps), "r1", wf_input=1)
    assert run.status is WorkflowStatus.COMPLETED
    assert run.outputs == {"a": 2, "b": 20}


def test_wiederaufnahme_ueberspringt_erledigte_schritte():
    calls = {"a": 0, "b": 0}

    def a(inp, ctx):
        calls["a"] += 1
        return "A"

    def b_first(inp, ctx):
        calls["b"] += 1
        raise RuntimeError("Absturz in b")

    journal = InMemoryJournal()
    engine = LocalWorkflowEngine(journal=journal)
    wf1 = WorkflowDef("wf", (WorkflowStep("a", a), WorkflowStep("b", b_first, RetryPolicy(max_attempts=1))))
    run1 = engine.run(wf1, "r1", None)
    assert run1.status is WorkflowStatus.FAILED and run1.failed_step == "b"
    assert calls["a"] == 1  # a lief einmal

    # Neustart mit gleicher run_id: a wird NICHT erneut ausgeführt (Journal), b jetzt ok.
    wf2 = WorkflowDef("wf", (WorkflowStep("a", a), WorkflowStep("b", lambda inp, ctx: "B")))
    run2 = engine.run(wf2, "r1", None)
    assert run2.status is WorkflowStatus.COMPLETED
    assert calls["a"] == 1  # immer noch nur einmal -> idempotent/wiederaufgenommen
    assert run2.outputs == {"a": "A", "b": "B"}


def test_retry_mit_backoff_dann_erfolg():
    versuche = {"n": 0}
    schlaf = []

    def flaky(inp, ctx):
        versuche["n"] += 1
        if versuche["n"] < 3:
            raise RuntimeError("flüchtig")
        return "ok"

    engine = LocalWorkflowEngine(sleep=schlaf.append)
    wf = WorkflowDef("wf", (WorkflowStep("s", flaky, RetryPolicy(max_attempts=3, base_delay=0.5, factor=2.0)),))
    run = engine.run(wf, "r1", None)
    assert run.status is WorkflowStatus.COMPLETED
    assert versuche["n"] == 3
    assert run.attempts["s"] == 3
    assert schlaf == [0.5, 1.0]  # Backoff vor Versuch 2 und 3


def test_permanenter_fehler_wird_failed():
    engine = LocalWorkflowEngine()
    wf = WorkflowDef("wf", (WorkflowStep("s", lambda i, c: (_ for _ in ()).throw(ValueError("kaputt")),
                                         RetryPolicy(max_attempts=2)),))
    run = engine.run(wf, "r1", None)
    assert run.status is WorkflowStatus.FAILED and "kaputt" in run.error


# ---------------- Trigger ----------------
def test_interval_trigger():
    t = IntervalTrigger(every_seconds=60)
    assert t.should_fire(None, now=1000) is True       # erstes Mal
    assert t.should_fire(1000, now=1030) is False      # zu früh
    assert t.should_fire(1000, now=1061) is True       # Intervall erreicht


def test_daily_trigger_feuert_einmal_pro_tag():
    t = DailyTrigger(hour=9, minute=0)
    day = 20_000 * 86_400  # irgendein Tagesbeginn (UTC)
    vor9 = day + 8 * 3600
    nach9 = day + 9 * 3600 + 5
    nach9_spaeter = day + 15 * 3600
    naechster_tag_9 = day + 86_400 + 9 * 3600
    assert t.should_fire(None, vor9) is False
    assert t.should_fire(None, nach9) is True
    assert t.should_fire(nach9, nach9_spaeter) is False   # heute schon gefeuert
    assert t.should_fire(nach9, naechster_tag_9) is True   # nächster Tag


def test_event_und_webhook_trigger():
    assert EventTrigger("rechnung.erstellt").matches({"name": "rechnung.erstellt"}) is True
    assert EventTrigger("x").matches({"name": "y"}) is False
    assert WebhookTrigger("/hooks/stripe").matches("/hooks/stripe/") is True
    assert WebhookTrigger("/a").matches("/b") is False


def test_idempotency_guard():
    g = IdempotencyGuard()
    assert g.first_time("evt-1") is True
    assert g.first_time("evt-1") is False   # zweite gleiche Auslösung -> ignoriert
    assert g.first_time("evt-2") is True


# ---------------- Temporal-Adapter ----------------
def test_temporal_retry_mapping():
    assert temporal_available() is True     # temporalio installiert
    tr = to_temporal_retry(RetryPolicy(max_attempts=5, base_delay=0.25, factor=3.0))
    assert tr.maximum_attempts == 5
    assert tr.initial_interval.total_seconds() == 0.25
    assert tr.backoff_coefficient == 3.0
