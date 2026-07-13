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
