"""Tests for the bundled jarvis_ultra_ticker plugin."""

from __future__ import annotations

import json
from pathlib import Path

from open_jarvis.plugins.loader import dispatch_plugin_command, load_plugin
from open_jarvis.plugins.manifest import validate_plugin_manifest_schema
from open_jarvis.plugins.registry import build_plugin_registry

PLUGIN_DIR = Path(__file__).resolve().parents[2] / "plugins" / "jarvis_ultra_ticker"


def test_manifest_is_valid_and_low_risk() -> None:
    manifest = json.loads((PLUGIN_DIR / "plugin.json").read_text(encoding="utf-8"))
    result = validate_plugin_manifest_schema(manifest, plugin_dir=PLUGIN_DIR)
    assert result["valid"], result["issues"]
    assert result["id"] == "jarvis_ultra_ticker"
    assert result["risk"] == "low"
    assert result["legacy"] is False


def test_registry_discovers_bundled_plugin() -> None:
    registry = build_plugin_registry(PLUGIN_DIR.parent)
    ids = [entry["id"] for entry in registry["plugins"]]
    assert "jarvis_ultra_ticker" in ids


def test_plugin_loads_and_answers_ticker_command() -> None:
    registry = build_plugin_registry(PLUGIN_DIR.parent)
    entry = next(item for item in registry["plugins"] if item["id"] == "jarvis_ultra_ticker")
    entry["enabled"] = True
    loaded = load_plugin(entry)
    assert loaded["status"] == "loaded", loaded
    context = loaded["context"]
    assert "ticker" in context.commands

    results = dispatch_plugin_command([loaded], "ticker")
    assert results and results[0]["status"] == "ok"
    assert any("EINSTELLUNG" in note["message"] or "·" in note["message"] for note in context.notifications)

    results = dispatch_plugin_command([loaded], "loadout")
    assert results[0]["status"] == "ok"
    assert any("16 Plugins" in note["message"] for note in context.notifications)
