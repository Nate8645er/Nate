"""Tests fuer den JARVIS-Agenten: Planer, Werkzeuge, Ausfuehrung, Sicherheit."""

from __future__ import annotations

import json

import pytest

from open_jarvis.agent import JarvisAgent, build_default_registry
from open_jarvis.agent.claude_provider import ClaudeProvider
from open_jarvis.agent.planner import ClaudePlanner, LocalPlanner
from open_jarvis.agent.tools import ToolContext, build_default_registry as build_reg


# --------------------------- LocalPlanner --------------------------------- #
def test_local_planner_detects_shop() -> None:
    plan = LocalPlanner().plan("baue mir einen Shop fuer Kaffee namens Bergbohne", build_reg())
    assert plan.steps[0]["tool"] == "shop_bauen"
    assert plan.steps[0]["args"]["name"] == "Bergbohne"
    assert plan.steps[0]["args"]["sells"] == "Kaffee"


def test_local_planner_detects_search_and_website() -> None:
    reg = build_reg()
    assert LocalPlanner().plan("suche nach Fluegen", reg).steps[0]["tool"] == "web_suche"
    assert LocalPlanner().plan("oeffne die webseite github.com", reg).steps[0]["tool"] == "webseite"


def test_local_planner_never_empty() -> None:
    plan = LocalPlanner().plan("irgendwas voellig unklares xyz", build_reg())
    assert plan.steps  # Fallback-Notiz, nie leer


# --------------------------- Agent-Ausfuehrung ---------------------------- #
def test_agent_preview_does_not_write(tmp_path) -> None:
    agent = JarvisAgent(model="local", workspace=tmp_path, execute=False)
    run = agent.run("baue mir einen Shop fuer Sneaker")
    assert run.ok
    assert run.outcomes[0].tool == "shop_bauen"
    assert not run.outcomes[0].result.executed
    assert list(tmp_path.iterdir()) == []  # Vorschau schreibt nichts


def test_agent_execute_writes_shop(tmp_path) -> None:
    agent = JarvisAgent(model="local", workspace=tmp_path, execute=True)
    run = agent.run("baue mir einen Shop fuer Kaffee namens Bergbohne")
    assert run.ok
    outcome = run.outcomes[0]
    assert outcome.result.executed
    shop_dir = tmp_path / "shops" / "bergbohne"
    assert (shop_dir / "shop_plan.md").exists()
    data = json.loads((shop_dir / "shop_plan.json").read_text(encoding="utf-8"))
    assert data["name"] == "Bergbohne"
    assert len(data["products"]) == 8


def test_agent_run_serializes_to_dict(tmp_path) -> None:
    run = JarvisAgent(model="local", workspace=tmp_path).run("suche nach Kaffee")
    payload = run.to_dict()
    assert payload["model"] == "local"
    assert payload["steps"][0]["tool"] == "web_suche"
    json.dumps(payload)  # muss serialisierbar sein


# --------------------------- Werkzeug-Sicherheit -------------------------- #
def test_file_tool_rejects_path_escape(tmp_path) -> None:
    reg = build_reg()
    ctx = ToolContext(workspace=tmp_path, execute=True)
    result = reg["datei_schreiben"].handler({"path": "../../etc/passwd", "content": "x"}, ctx)
    assert result.ok is False
    assert not (tmp_path.parent / "etc").exists()


def test_website_tool_rejects_unsafe_url(tmp_path) -> None:
    reg = build_reg()
    ctx = ToolContext(workspace=tmp_path)
    result = reg["webseite"].handler({"url": "javascript:alert(1)"}, ctx)
    assert result.ok is False


def test_plugins_tool_reads_catalog(tmp_path) -> None:
    reg = build_reg()
    ctx = ToolContext(workspace=tmp_path)
    result = reg["plugins"].handler({}, ctx)
    assert result.ok
    assert result.data["total"] == 128


# --------------------------- Claude/Fable-Pfad ---------------------------- #
def test_claude_planner_falls_back_without_key() -> None:
    from open_jarvis.agent.models import resolve_model

    provider = ClaudeProvider(model_id="claude-fable-5", api_key="")  # kein Schluessel
    planner = ClaudePlanner(resolve_model("fable-5"), provider=provider)
    plan = planner.plan("baue einen Shop fuer Tee", build_reg())
    assert plan.steps[0]["tool"] == "shop_bauen"
    assert "local" in plan.planner  # Fallback markiert
    assert "ANTHROPIC_API_KEY" in plan.note


def test_claude_planner_uses_model_when_key_present() -> None:
    from open_jarvis.agent.models import resolve_model

    def fake_transport(url, payload, headers):
        assert payload["model"] == "claude-fable-5"
        assert headers["x-api-key"] == "k"
        return {"content": [{"type": "text", "text": json.dumps({
            "steps": [{"tool": "web_suche", "args": {"query": "tee"}, "why": "test"}],
            "final": "erledigt",
        })}]}

    provider = ClaudeProvider(model_id="claude-fable-5", api_key="k", transport=fake_transport)
    planner = ClaudePlanner(resolve_model("fable-5"), provider=provider)
    plan = planner.plan("suche tee", build_reg())
    assert plan.planner == "fable-5"
    assert plan.steps[0]["tool"] == "web_suche"
    assert plan.final == "erledigt"


def test_claude_planner_rejects_unknown_tools_from_model() -> None:
    from open_jarvis.agent.models import resolve_model

    def fake_transport(url, payload, headers):
        return {"content": [{"type": "text", "text": json.dumps({
            "steps": [{"tool": "rm_rf", "args": {}, "why": "boese"}],
            "final": "x",
        })}]}

    provider = ClaudeProvider(model_id="claude-fable-5", api_key="k", transport=fake_transport)
    planner = ClaudePlanner(resolve_model("fable-5"), provider=provider)
    plan = planner.plan("mach was", build_reg())
    # Unbekanntes Werkzeug -> lokaler Fallback, kein rm_rf im Plan
    assert all(step["tool"] != "rm_rf" for step in plan.steps)
    assert "local" in plan.planner
