"""Tests fuer die "Alles aktivieren"-Funktion."""

from __future__ import annotations

import json

from open_jarvis.agent.activate import (
    PLUGINS_ROOT,
    activate_all_plugins,
    activation_report,
    full_activation,
    render_activation,
    render_full_activation,
)


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


# --------------------------- Voll-Aktivierung (Workforce) ------------------- #
def test_full_activation_activates_whole_workforce(tmp_path) -> None:
    a = full_activation(state_file=tmp_path / "state.json")
    assert a["fully_active"] is True
    assert a["plugins_enabled"] == 129
    assert a["brain"] == "Fable 5"
    # Kennzahlen exakt (Python-Ganzzahlen)
    assert a["employees_active"] == 10**12
    assert a["companies_active"] == 10**12
    assert a["company_employees_active"] == 10**24
    assert a["developers_active"] == 10**24
    assert a["total_workforce_active"] == 10**12 + 2 * 10**24


def test_full_activation_capability_math_is_exact(tmp_path) -> None:
    a = full_activation(state_file=tmp_path / "state.json")
    per = 200 + 128 + 192 + 6 + 15 + 20  # Skills+Plugins+Tools+Modelle+Agent+Shopify
    assert a["capabilities_per_entity"] == per
    assert a["capabilities_per_entity"] == 561
    assert a["total_capabilities_active"] == per * (10**12 + 2 * 10**24)


def test_render_full_activation_text(tmp_path) -> None:
    text = render_full_activation(full_activation(state_file=tmp_path / "state.json"))
    assert "VOLL-AKTIVIERUNG" in text
    assert "1.000.000.000.000" in text          # 10^12 mit dt. Trennpunkten
    assert "2.000.000.000.001.000.000.000.000" in text  # Gesamt-Workforce
    assert "Fable 5" in text
