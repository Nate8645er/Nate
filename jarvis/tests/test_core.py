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
