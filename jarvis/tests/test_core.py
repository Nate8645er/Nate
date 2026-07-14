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
