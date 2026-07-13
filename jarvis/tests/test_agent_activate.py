"""Tests fuer die "Alles aktivieren"-Funktion."""

from __future__ import annotations

import json

from open_jarvis.agent.activate import activate_all_plugins, activation_report, render_activation, PLUGINS_ROOT


def test_activate_all_enables_every_plugin(tmp_path) -> None:
    state_file = tmp_path / "state.json"
    result = activate_all_plugins(state_file=state_file)
    assert result["activated"] == 129
    assert result["total"] == 129
    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert sum(1 for v in data["plugins"].values() if v.get("enabled")) == 129
    # Audit-Eintrag vorhanden
    assert any(a.get("action") == "activate-all" for a in data["audit"])


def test_activation_report_fully_active_after_activation(tmp_path) -> None:
    state_file = tmp_path / "state.json"
    activate_all_plugins(state_file=state_file)
    report = activation_report(state_file=state_file)
    assert report["plugins_enabled"] == 129
    assert report["plugins_total"] == 129
    assert report["fully_active"] is True
    assert report["brain"] == "Fable 5"
    assert report["models"] == 6
    assert report["skills"] == 200
    assert report["tools"] == 192


def test_activation_report_not_active_without_state(tmp_path) -> None:
    report = activation_report(state_file=tmp_path / "leer.json")
    assert report["plugins_enabled"] == 0
    assert report["fully_active"] is False


def test_render_activation_text(tmp_path) -> None:
    state_file = tmp_path / "state.json"
    activate_all_plugins(state_file=state_file)
    text = render_activation(activation_report(state_file=state_file))
    assert "129/129" in text
    assert "ALLES AKTIV" in text
    assert "Fable 5" in text


def test_plugins_root_exists() -> None:
    assert PLUGINS_ROOT.is_dir()
