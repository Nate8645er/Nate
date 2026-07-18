"""Boss/Worker-Aufteilung: Fable 5 orchestriert, GPT-5.6 Sol Ultra arbeitet."""
from __future__ import annotations

from jarvis.core import brain, openrouter
from jarvis.core.identity import materialize


def test_worker_uses_sol_ultra_via_openrouter(monkeypatch):
    """role=worker + OpenRouter-Key -> Aufruf geht an das Worker-Modell (Sol Ultra)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "or")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    seen = {}

    def fake_ask(model, prompt, system="", max_tokens=600, timeout=120):
        seen["model"] = model
        return "Worker-Antwort von Sol"

    monkeypatch.setattr(openrouter, "ask", fake_ask)
    out = brain.answer(materialize("500"), "erledige das", role="worker")
    assert out == "Worker-Antwort von Sol"
    assert seen["model"] == brain.WORKER_MODEL == "openai/gpt-5.6-sol-ultra"


def test_worker_falls_back_to_boss_without_openrouter(monkeypatch):
    """Kein OpenRouter-Key -> Worker fällt still auf das Boss-Gehirn (Fable 5) zurück."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant")
    brain._active_model = None

    def fake_call(model, system, user, max_tokens=600):
        return f"Boss-Antwort ({model})"

    monkeypatch.setattr(brain, "_call", fake_call)
    out = brain.answer(materialize("500"), "erledige das", role="worker")
    assert out.startswith("Boss-Antwort")          # kein Sol -> Fable 5 übernimmt


def test_worker_openrouter_error_falls_back_to_boss(monkeypatch):
    """Sol/OpenRouter-Fehler -> ehrlicher Rückfall auf das Boss-Gehirn, kein Crash."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "or")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant")
    brain._active_model = None
    monkeypatch.setattr(openrouter, "ask",
                        lambda m, p, system="", max_tokens=600, timeout=120:
                        "[OpenRouter 429: Too Many Requests]")
    monkeypatch.setattr(brain, "_call",
                        lambda model, system, user, max_tokens=600: "Boss rettet")
    out = brain.answer(materialize("500"), "x", role="worker")
    assert out == "Boss rettet"


def test_boss_role_unchanged_uses_fable(monkeypatch):
    """role=boss (Standard) ignoriert Sol und nutzt das Fable-5-Gehirn direkt."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "or")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant")
    brain._active_model = None
    called = {"sol": 0}

    def fake_ask(model, prompt, system="", max_tokens=600, timeout=120):
        called["sol"] += 1
        return "sol"

    monkeypatch.setattr(openrouter, "ask", fake_ask)
    monkeypatch.setattr(brain, "_call",
                        lambda model, system, user, max_tokens=600: "Fable-Boss")
    out = brain.answer(materialize("500"), "führe zusammen", role="boss")
    assert out == "Fable-Boss" and called["sol"] == 0   # Boss geht nie an Sol


def test_worker_active_flag(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert brain.worker_active() is False
    monkeypatch.setenv("OPENROUTER_API_KEY", "or")
    assert brain.worker_active() is True
    monkeypatch.setenv("JARVIS_WORKER_MODEL", "off")
    # Modul-Konstante ist zur Importzeit gesetzt; Abschaltung wirkt über die Konstante.
    brain.WORKER_MODEL = "off"
    assert brain.worker_active() is False
    brain.WORKER_MODEL = "openai/gpt-5.6-sol-ultra"


def test_orchestrator_routes_task_through_worker(monkeypatch, tmp_path):
    """End-to-End: eine eingereichte Aufgabe wird als Worker (Sol Ultra) bearbeitet."""
    import asyncio

    from jarvis.core import openrouter
    from jarvis.core.orchestrator import Orchestrator

    monkeypatch.setenv("OPENROUTER_API_KEY", "or")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    seen = {"models": []}

    def fake_ask(model, prompt, system="", max_tokens=600, timeout=120):
        seen["models"].append(model)
        return f"[Sol] erledigt: {prompt[:20]}"

    monkeypatch.setattr(openrouter, "ask", fake_ask)

    async def run():
        o = Orchestrator(tmp_path, max_active=2)
        await o.start()
        t = o.submit("Schreibe eine Zeile Text", address="500")
        for _ in range(60):
            if t.status in ("fertig", "fehler"):
                break
            await asyncio.sleep(0.05)
        await o.stop()
        return t

    t = asyncio.run(run())
    assert t.status == "fertig"
    assert t.result.startswith("[Sol]")
    assert "openai/gpt-5.6-sol-ultra" in seen["models"]


def test_autopilot_idea_runs_as_worker(monkeypatch, tmp_path):
    """Autopilot-Ideen sind Worker-Arbeit -> role=worker (Sol Ultra)."""
    from jarvis.core import autopilot as ap_mod

    seen = {}

    def fake_answer(emp, prompt, role="boss"):
        seen["role"] = role
        return "TITEL: Test\nIDEE: x\nZIELGRUPPE: y\nERSTER SCHRITT: z"

    monkeypatch.setattr(ap_mod.brain, "answer", fake_answer)
    ap = ap_mod.Autopilot(tmp_path, interval_s=999)
    ap.on = True
    ap._gen = 1
    # Einen einzelnen Durchlauf ausführen, dann stoppen.
    import threading
    t = threading.Thread(target=ap._run, args=(1,))
    t.start()
    import time as _t
    for _ in range(50):
        if ap.count_total >= 1:
            break
        _t.sleep(0.02)
    ap.on = False
    ap._gen = 2
    t.join(timeout=2)
    assert seen.get("role") == "worker"
    assert ap.count_total >= 1


def test_default_role_is_boss(monkeypatch):
    """Direkte answer()-Aufrufe ohne role bleiben Boss (Rückwärtskompatibilität)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "or")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "ant")
    brain._active_model = None
    monkeypatch.setattr(openrouter, "ask",
                        lambda m, p, system="", max_tokens=600, timeout=120: "sol")
    monkeypatch.setattr(brain, "_call",
                        lambda model, system, user, max_tokens=600: "fable")
    assert brain.answer(materialize("1"), "frage") == "fable"   # default = boss
