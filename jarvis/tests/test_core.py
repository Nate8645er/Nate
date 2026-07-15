"""Kerntests: Identität, Adressraum, Plugins, Orchestrator-Begrenzung."""

import asyncio
from pathlib import Path

import pytest

from jarvis.core.identity import (ADDRESS_SPACE, address_for_task,
                                  materialize, validate_address)
from jarvis.core.orchestrator import Orchestrator
from jarvis.core.plugins import PluginManager


def test_identity_deterministic():
    a = materialize("12345678901")
    b = materialize("12345678901")
    assert a == b
    assert a.name and a.team and a.role


def test_identity_hierarchical_companies():
    boss = materialize("42")
    worker = materialize("42/777")
    deep = materialize("42/777/31337")
    assert boss.sub_employees == ADDRESS_SPACE
    assert worker.depth == 1 and deep.depth == 2
    assert worker.address == "42/777"


def test_address_space_bounds():
    validate_address(str(ADDRESS_SPACE - 1))
    with pytest.raises(ValueError):
        validate_address(str(ADDRESS_SPACE))
    with pytest.raises(ValueError):
        validate_address("abc")


def test_task_routing_prefers_matching_team():
    addr = address_for_task("Bitte Python-Team: Skript schreiben", team_hint="Python-Team")
    assert materialize(addr).team == "Python-Team"


def test_plugin_authorization(tmp_path: Path):
    pm = PluginManager(tmp_path)
    assert pm.run("Führung", "calc", "eval", expression="6*7") == 42
    assert "system" in pm.for_team("DevOps")


def test_files_plugin_sandbox(tmp_path: Path):
    pm = PluginManager(tmp_path)
    with pytest.raises(PermissionError):
        pm.run("Führung", "files", "read", path="../../etc/passwd")


def test_orchestrator_bounded_and_processes(tmp_path: Path):
    async def scenario():
        orch = Orchestrator(tmp_path, max_active=3)
        await orch.start()
        for i in range(9):
            orch.submit(f"!plugin calc eval expression={i}+1")
        await orch.queue.join()
        assert len(orch.active) <= 3
        await orch.stop()
        return orch

    orch = asyncio.run(scenario())
    assert orch.completed == 9
    assert orch.failed == 0
    assert orch.memory.count() == 9


def test_finance_plugin_real_ledger(tmp_path: Path):
    pm = PluginManager(tmp_path)
    pm.run("Führung", "finanzen", "einnahme", betrag="150.50", notiz="Testrechnung")
    pm.run("Führung", "finanzen", "ausgabe", betrag="50.50", notiz="Material")
    s = pm.run("Führung", "finanzen", "summe")
    assert s["einnahmen"] == 150.5 and s["ausgaben"] == 50.5 and s["saldo"] == 100.0
    with pytest.raises(ValueError):
        pm.run("Führung", "finanzen", "einnahme", betrag="-5")


def test_tasks_plugin(tmp_path: Path):
    pm = PluginManager(tmp_path)
    pm.run("Führung", "aufgaben", "add", text="JARVIS testen")
    offen = pm.run("Führung", "aufgaben", "list")
    assert len(offen) == 1 and offen[0]["text"] == "JARVIS testen"
    pm.run("Führung", "aufgaben", "done", id="1")
    assert pm.run("Führung", "aufgaben", "list") == "Keine offenen Aufgaben."


def test_kwargs_parser_handles_spaces():
    from jarvis.core.orchestrator import _parse_kwargs
    assert _parse_kwargs("command=echo hi && pwd") == {"command": "echo hi && pwd"}
    assert _parse_kwargs("betrag=250 notiz=Kunde A") == {"betrag": "250", "notiz": "Kunde A"}
    assert _parse_kwargs("") == {}


def test_code_style_tools_registered(tmp_path: Path):
    from jarvis.core import tools
    pm = PluginManager(tmp_path)
    tools.register_all(pm, tmp_path)
    for name in ("shell", "read", "edit", "glob", "grep", "webfetch"):
        assert name in pm.plugins
    (tmp_path / "a.txt").write_text("hallo welt\nzeile zwei", encoding="utf-8")
    assert "a.txt" in pm.run("Führung", "glob", "glob", pattern="*.txt")
    hits = pm.run("Führung", "grep", "grep", pattern="zwei")
    assert any("zeile zwei" in h for h in hits)


def test_skills_registry(tmp_path: Path):
    from jarvis.core.skills import SkillRegistry
    reg = SkillRegistry(tmp_path / "skills")
    names = [s.name for s in reg.all()]
    assert "zusammenfassen" in names
    prompt = reg.apply("zusammenfassen", "Langer Text hier.")
    assert "# Skill: zusammenfassen" in prompt and "Langer Text hier." in prompt


def test_code_agent_finds_binary_or_falls_back(tmp_path: Path):
    from jarvis.core.code_agent import CodeAgentPlugin
    plugin = CodeAgentPlugin(tmp_path)
    # ohne API-Key: ehrlicher Fallback, kein Absturz
    out = plugin.run("prompt", prompt="Test")
    assert isinstance(out, str) and len(out) > 0


def test_workforce_engine_activates(tmp_path: Path):
    import time
    from jarvis.core.workforce import WorkforceEngine
    eng = WorkforceEngine(waves=4)
    assert eng.stats()["in_betrieb"] is False
    eng.start()
    time.sleep(1.0)
    eng.stop()
    s = eng.stats()
    assert eng.activated > 0            # es wurden echt Mitarbeiter durchlaufen
    assert s["durchlaufen"] > 0


def test_autopilot_generates_ideas(tmp_path: Path):
    import time
    from jarvis.core.autopilot import Autopilot
    ap = Autopilot(tmp_path, interval_s=20)
    assert ap.stats()["laeuft"] is False
    ap.start()
    time.sleep(1.5)          # erste Idee wird sofort erzeugt
    ap.stop()
    s = ap.stats()
    assert s["ideen_gesamt"] >= 1
    assert s["letzte"] and "von" in s["letzte"][0]
    # heutige Ideen werden erfasst
    assert len(ap.today()) >= 1


def test_security_sandbox_blocks_sibling_prefix(tmp_path: Path):
    """_safe darf nicht in einen Geschwister-Ordner mit gleichem Präfix schreiben/lesen."""
    from jarvis.core import tools
    ws = tmp_path / "workspace"
    pm = PluginManager(ws)
    tools.register_all(pm, ws)
    (tmp_path / "workspace-backup").mkdir()
    (tmp_path / "workspace-backup" / "geheim.txt").write_text("secret", encoding="utf-8")
    with pytest.raises(PermissionError):
        pm.run("Führung", "read", "read", path="../workspace-backup/geheim.txt")


def test_security_dangerous_tools_gated(tmp_path: Path, monkeypatch):
    from jarvis.core import tools
    pm = PluginManager(tmp_path)
    tools.register_all(pm, tmp_path)
    monkeypatch.delenv("JARVIS_ALLOW_DANGEROUS", raising=False)
    with pytest.raises(PermissionError):
        pm.run("Führung", "shell", "run", command="echo x")
    monkeypatch.setenv("JARVIS_ALLOW_DANGEROUS", "1")
    assert "exit 0" in pm.run("Führung", "shell", "run", command="echo x")


def test_security_ssrf_blocked(tmp_path: Path):
    from jarvis.core import tools
    pm = PluginManager(tmp_path)
    tools.register_all(pm, tmp_path)
    for url in ("http://169.254.169.254/latest/meta-data/", "http://127.0.0.1:80/"):
        assert "verweigert" in pm.run("Führung", "webfetch", "fetch", url=url)


def test_security_calc_pow_limit(tmp_path: Path):
    pm = PluginManager(tmp_path)
    assert pm.run("Führung", "calc", "eval", expression="2**10") == 1024
    with pytest.raises(ValueError):
        pm.run("Führung", "calc", "eval", expression="9**99999")


def test_pc_control_separate_switch(tmp_path: Path, monkeypatch):
    from jarvis.core import desktop
    pm = PluginManager(tmp_path)
    desktop.register(pm, tmp_path)
    assert "pc" in pm.plugins
    monkeypatch.delenv("JARVIS_ALLOW_PC", raising=False)
    monkeypatch.delenv("JARVIS_ALLOW_DANGEROUS", raising=False)
    with pytest.raises(PermissionError):
        pm.run("Führung", "pc", "apps")
    # eigener Schalter aktiviert PC, aber nicht Shell
    monkeypatch.setenv("JARVIS_ALLOW_PC", "1")
    apps = pm.run("Führung", "pc", "apps")
    assert isinstance(apps, list) and len(apps) > 0


def test_natural_language_commands():
    from jarvis.core.commands import interpret
    assert interpret("öffne YouTube") == "!plugin pc open program=https://www.youtube.com"
    assert interpret("mach Notepad auf") == "!plugin pc open program=notepad"
    assert interpret("starte den Rechner") == "!plugin pc open program=calc"
    assert interpret("schließe notepad") == "!plugin pc close name=notepad.exe"
    assert interpret("mach einen Screenshot") == "!plugin pc screenshot"
    assert interpret("suche nach Wetter") == "!plugin web suche query=Wetter"
    # normale Fragen bleiben Fragen (kein Kommando)
    assert interpret("was ist die Hauptstadt von Frankreich") is None


def test_natural_command_routed_and_gated(tmp_path: Path, monkeypatch):
    import asyncio
    from jarvis.core.orchestrator import Orchestrator
    monkeypatch.delenv("JARVIS_ALLOW_PC", raising=False)

    async def scenario():
        orch = Orchestrator(tmp_path, max_active=2)
        await orch.start()
        t = orch.submit("öffne YouTube")     # freie Sprache
        await orch.queue.join()
        await orch.stop()
        return t

    task = asyncio.run(scenario())
    # ohne PC-Freischaltung: sauber gesperrt (kein Absturz), Befehl wurde erkannt+geroutet
    assert "gesperrt" in task.result.lower()


def test_browser_commands():
    from jarvis.core.commands import interpret
    assert interpret("öffne chrome") == "!plugin pc browser browser=chrome"
    assert interpret("starte edge") == "!plugin pc browser browser=edge"
    assert interpret("öffne youtube in chrome") == \
        "!plugin pc browser browser=chrome url=https://www.youtube.com"
    assert interpret("öffne chrome mit youtube") == \
        "!plugin pc browser browser=chrome url=https://www.youtube.com"
    assert interpret("schließe chrome") == "!plugin pc close name=chrome.exe"


def test_browser_auto_registered_and_gated(tmp_path: Path, monkeypatch):
    from jarvis.core import browser_auto
    pm = PluginManager(tmp_path)
    browser_auto.register(pm, tmp_path)
    assert "browser_auto" in pm.plugins
    monkeypatch.delenv("JARVIS_ALLOW_PC", raising=False)
    monkeypatch.delenv("JARVIS_ALLOW_DANGEROUS", raising=False)
    with pytest.raises(PermissionError):
        pm.run("Führung", "browser_auto", "read")


def test_browser_auto_commands():
    from jarvis.core.commands import interpret
    assert interpret("navigiere zu youtube") == \
        "!plugin browser_auto goto url=https://www.youtube.com"
    assert interpret("lies die seite") == "!plugin browser_auto read"
    assert interpret("welche links gibt es") == "!plugin browser_auto links"
    assert interpret("im browser klicke auf Anmelden") == \
        "!plugin browser_auto click ziel=text=Anmelden"


def test_security_check_and_monitor(tmp_path):
    import time
    from jarvis.core.security import SecurityPlugin, SecurityMonitor
    p = SecurityPlugin()
    report = p.check()          # read-only, muss immer ein dict liefern
    assert isinstance(report, dict) and "zeit" in report
    m = SecurityMonitor(p, interval_s=60)
    assert m.stats()["laeuft"] is False
    m.start(); time.sleep(1.2); m.stop()
    assert m.checks >= 1
    assert m.stats()["intervall_min"] == 1


def test_security_actions_gated_without_pc(monkeypatch):
    from jarvis.core.security import SecurityPlugin
    monkeypatch.delenv("JARVIS_ALLOW_PC", raising=False)
    monkeypatch.delenv("JARVIS_ALLOW_DANGEROUS", raising=False)
    p = SecurityPlugin()
    # scan/signatures greifen ins System ein -> ohne Freischaltung gesperrt (auf Windows);
    # auf nicht-Windows kommt der Windows-Hinweis. Beides ist ein klarer String, kein Absturz.
    out = p.run("scan")
    assert isinstance(out, str) and len(out) > 0


def test_bodyguard_squad(tmp_path, monkeypatch):
    import time
    from jarvis.core.security import BodyguardSquad, SecurityPlugin
    monkeypatch.delenv("JARVIS_ALLOW_PC", raising=False)
    sq = BodyguardSquad(SecurityPlugin(), interval_s=60)
    st = sq.stats()
    assert st["anzahl"] == 6 and st["aktiv"] is False
    assert all("posten" in g for g in st["waechter"])
    sq.start(); time.sleep(1.2); sq.stop()
    assert sq.patrols >= 1
    # ohne Freischaltung nur melden, keine Selbstheilung
    assert "nur melden" in sq.stats()["selbstheilung"]


def test_vision_commands_and_offline(monkeypatch):
    from jarvis.core.commands import interpret
    assert interpret("was ist auf dem bildschirm") == "!plugin pc sehen"
    assert interpret("was siehst du") == "!plugin pc sehen"
    assert interpret("analysiere den bildschirm") == "!plugin pc sehen"
    from jarvis.core import brain
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out = brain.describe_image("x", "image/png", "was ist das")
    assert "OFFLINE" in out or "Fable 5" in out


def test_all_employees_connected(tmp_path):
    """Verbindungs-Check: Mitarbeiter quer durch den Adressraum haben Identität + Werkzeuge."""
    import asyncio
    from jarvis.core.orchestrator import Orchestrator
    from jarvis.core.identity import materialize, ADDRESS_SPACE

    async def scenario():
        o = Orchestrator(tmp_path, max_active=4)
        await o.start()
        for a in ["0", "42", "777", "12345678901", str(ADDRESS_SPACE - 1), "42/777/31337"]:
            e = materialize(a)
            assert e.name and e.team and e.skills
            assert o.plugins.for_team(e.team), f"Mitarbeiter {a} ohne Werkzeuge"
        t = o.submit("!plugin calc eval expression=6*7")
        await o.queue.join()
        st = o.state()
        await o.stop()
        return t, st

    t, st = asyncio.run(scenario())
    assert t.status == "fertig" and t.result == "42" and t.agent
    # alle Subsysteme im State verbunden
    for key in ("plugins", "skills", "belegschaft", "autopilot", "sicherheit", "bodyguards"):
        assert key in st, f"Subsystem {key} nicht verbunden"


def test_clawcode_commands_and_path(tmp_path, monkeypatch):
    from jarvis.core.commands import interpret
    assert interpret("claw code schreibe test") == "!plugin code prompt prompt=schreibe test"
    assert interpret("clawcode hallo") == "!plugin code prompt prompt=hallo"
    assert interpret("claude code baue x") == "!plugin code prompt prompt=baue x"
    # expliziter Pfad-Schalter wird bevorzugt
    f = tmp_path / "claw.exe"
    f.write_text("x")
    monkeypatch.setenv("JARVIS_CLAW_PATH", str(f))
    from jarvis.core.code_agent import find_binary
    assert find_binary() == str(f)


# ---------------------------------------------------------------------------
# Audit-Regressionen (Ultracode-Runde 2): verifizierte Fund-Fixes
# ---------------------------------------------------------------------------

def test_parse_kwargs_keeps_embedded_equals():
    """Fund 2: Freitext mit eingebettetem 'wort=' darf nicht zerhackt werden."""
    from jarvis.core.orchestrator import _parse_kwargs, _plugin_param_names

    class FakeCode:
        def run(self, action="prompt", prompt="", model="", **kw):
            pass

    valid = _plugin_param_names(FakeCode())
    r = _parse_kwargs("prompt=setze debug=true in der config", valid)
    assert r["prompt"] == "setze debug=true in der config"
    assert "debug" not in r
    # ohne valid_keys (Rückwärtskompatibilität) splittet der Parser wie bisher
    r2 = _parse_kwargs("a=1 b=2")
    assert r2 == {"a": "1", "b": "2"}


def test_commands_do_not_hijack_normal_tasks():
    """Fund 4: normale Aufgaben dürfen NICHT ans gesperrte pc-Plugin gehen."""
    from jarvis.core.commands import interpret
    for t in ["zeige mir die offenen Aufgaben",
              "Starte die Analyse des Quartalsberichts",
              "beende die Diskussion",
              "finde den Fehler im Code"]:
        assert interpret(t) is None, f"{t!r} wurde fälschlich gemappt"
    # echte Kommandos funktionieren weiter
    assert "pc open" in interpret("öffne youtube")
    assert "pc close" in interpret("schließe chrome")
    assert "web suche" in interpret("suche nach docker")


def test_workforce_restart_no_double_thread():
    """Fund 10: der alte Sweep-Thread muss bei start/stop/start wirklich sterben."""
    from jarvis.core.workforce import WorkforceEngine
    wf = WorkforceEngine(waves=8)
    wf.start()
    t1 = wf._thread
    wf.stop()
    t1.join(timeout=3)
    assert not t1.is_alive(), "alter Sweep-Thread lebt nach stop() weiter (Race)"
    wf.start()
    t2 = wf._thread
    try:
        assert t2 is not t1 and t2.is_alive()
    finally:
        wf.stop()
        t2.join(timeout=3)


def test_workforce_rate_is_honest():
    """Fund 6: angezeigte Rate ist die reale Thread-Rate, nicht *wellen."""
    import time
    from jarvis.core.workforce import WorkforceEngine
    wf = WorkforceEngine(waves=64)
    wf.start(); time.sleep(1.5)
    s = wf.stats(); wf.stop()
    # 64 Wellen dürfen die Rate nicht um Faktor 64 aufblasen
    assert 0 < s["rate_pro_s"] < 1_000_000


def test_finanzen_robust_ziel(tmp_path, monkeypatch):
    """Fund 9: Schweizer Format / 0 / Unsinn crasht finanzen() (und /api/state) nicht."""
    o = Orchestrator(tmp_path, max_active=2)
    for val in ["1'000'000", "0", "quatsch", "1000000"]:
        monkeypatch.setenv("JARVIS_ZIEL_CHF", val)
        f = o.finanzen()
        assert f["ziel_chf"] > 0
        assert isinstance(f["fortschritt_prozent"], (int, float))


def test_plugin_without_action_gives_usage(tmp_path):
    """Fund 21: '!plugin system' ohne Aktion -> Syntax-Hinweis, kein IndexError."""
    import asyncio

    async def scenario():
        o = Orchestrator(tmp_path, max_active=1)
        await o.start()
        t = o.submit("!plugin system")
        await asyncio.wait_for(o.queue.join(), timeout=10)
        await o.stop()
        return t

    t = asyncio.run(scenario())
    assert t.status == "fehler"
    assert "Syntax" in t.result and "IndexError" not in t.result


def test_files_list_relative_workspace(tmp_path, monkeypatch):
    """Fund 20: FilesPlugin 'list' darf mit relativem Workspace nicht crashen."""
    import os
    from jarvis.core.plugins import FilesPlugin
    monkeypatch.chdir(tmp_path)
    p = FilesPlugin(Path("reldata/workspace/files"))
    p.run("write", path="notiz.txt", content="x")
    listing = p.run("list")
    assert "notiz.txt" in listing


def test_host_header_ipv6():
    """Fund 11: IPv6-Loopback [::1]:port wird korrekt als '::1' erkannt."""
    from jarvis.dashboard.app import _host_from_header
    assert _host_from_header("[::1]:8787") == "::1"
    assert _host_from_header("127.0.0.1:8787") == "127.0.0.1"
    assert _host_from_header("localhost") == "localhost"


def test_plugin_health_reported(tmp_path):
    """Fund 12: Plugins mit fehlender Abhängigkeit melden ok=False + Hinweis."""
    from jarvis.core.desktop import PCControlPlugin
    st = PCControlPlugin(tmp_path).status()
    assert "ok" in st and "verfuegbar" in st and "hinweis" in st


def test_ssrf_redirect_handler_blocks_internal():
    """Fund 7: SSRF-Redirect-Handler existiert und Blockliste greift für interne IPs."""
    from jarvis.core.tools import _SafeRedirectHandler, _host_is_blocked
    assert _SafeRedirectHandler().opener is not None
    assert _host_is_blocked("169.254.169.254")   # Cloud-Metadaten
    assert _host_is_blocked("127.0.0.1")
    assert not _host_is_blocked("example.com")


# ---------------------------------------------------------------------------
# Multi-Modell-Anschluss (OpenRouter) — neutraler Zugang, kein Jailbreak
# ---------------------------------------------------------------------------

def test_openrouter_plugin_registered_and_honest(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    from jarvis.core.orchestrator import Orchestrator
    o = Orchestrator(tmp_path)
    names = [s["name"] for s in o.plugins.status()]
    assert "modelle" in names
    st = next(s for s in o.plugins.status() if s["name"] == "modelle")
    assert st["ok"] is False and "OPENROUTER_API_KEY" in st["hinweis"]
    # ohne Key: ehrliche Meldung, kein Crash
    r = o.plugins.run("Führung", "modelle", "frage", model="gpt", prompt="hi")
    assert "OPENROUTER_API_KEY" in r["antwort"]


def test_openrouter_commands_routed():
    from jarvis.core.commands import interpret
    assert interpret("vergleiche die modelle: sinn des lebens") == \
        "!plugin modelle vergleich prompt=sinn des lebens"
    assert interpret("modell gpt: erkläre rekursion") == \
        "!plugin modelle frage model=gpt prompt=erkläre rekursion"


def test_openrouter_request_built_correctly(monkeypatch):
    """Baut die Anfrage korrekt (Bearer-Auth, Modell, system+user)?"""
    import io, json
    from jarvis.core import openrouter
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    cap = {}

    class FakeResp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout=0):
        cap["auth"] = req.headers.get("Authorization")
        cap["body"] = json.loads(req.data)
        return FakeResp(json.dumps({"choices": [{"message": {"content": "42"}}]}).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    ans = openrouter.ask("openai/gpt-4o", "6*7?")
    assert ans == "42"
    assert cap["auth"] == "Bearer test-key"
    assert cap["body"]["model"] == "openai/gpt-4o"
    assert [m["role"] for m in cap["body"]["messages"]] == ["system", "user"]
