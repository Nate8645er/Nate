"""„Alles aktivieren" — schaltet alle mitgelieferten JARVIS-Plugins scharf.

Die 129 Katalog-Plugins gehoeren zum Repo (nicht fremde, unsignierte Drittanbieter),
deshalb ist ihre Aktivierung eine legitime lokale Nutzer-Aktion. Diese Funktion
schreibt den Enable-Zustand direkt in die Plugin-State-Datei (mit Audit-Eintrag),
sodass die Registry alle Plugins als ``enabled`` fuehrt.

CLI:  python3 -m open_jarvis.agent --activate-all
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from open_jarvis.agent.models import list_models
from open_jarvis.enterprise import catalog
from open_jarvis.plugins.plugin_state import DEFAULT_STATE_FILE, build_plugin_state
from open_jarvis.plugins.registry import build_plugin_registry

PLUGINS_ROOT = Path(__file__).resolve().parents[2] / "plugins"


def activate_all_plugins(
    *,
    root: Path | str = PLUGINS_ROOT,
    state_file: Path | str = DEFAULT_STATE_FILE,
    approved_by: str = "local-user",
) -> dict[str, Any]:
    """Alle entdeckten Plugins aktivieren (Enable-State + Audit schreiben)."""

    registry = build_plugin_registry(root)
    state = build_plugin_state(state_file)
    activated: list[str] = []
    for entry in registry["plugins"]:
        if entry["issues"]:
            continue  # defekte Plugins nicht aktivieren
        plugin_id = entry["id"]
        state["plugins"][plugin_id] = {
            "enabled": True,
            "version": entry.get("version", ""),
            "path": entry.get("path", ""),
            "approved_by": approved_by,
            "approval_reason": "activate-all (mitgeliefertes Katalog-Plugin)",
        }
        activated.append(plugin_id)
    state["audit"].append({"plugin": "*", "action": "activate-all", "approved_by": approved_by, "count": len(activated)})
    Path(state_file).write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "activated": len(activated),
        "total": len(registry["plugins"]),
        "state_file": str(state_file),
    }


def activation_report(*, root: Path | str = PLUGINS_ROOT, state_file: Path | str = DEFAULT_STATE_FILE) -> dict[str, Any]:
    """Vollstaendiger Aktivierungs-Ueberblick ueber JARVIS (fuer CLI/Dashboard)."""

    registry = build_plugin_registry(root, state_file=state_file)
    plugins = registry["plugins"]
    enabled = sum(1 for e in plugins if e["enabled"])
    summary = catalog.capability_summary()
    return {
        "plugins_total": len(plugins),
        "plugins_enabled": enabled,
        "plugins_available": len(plugins) - enabled,
        "skills": summary["skills"],
        "tools": summary["tools"],
        "models": summary["models"],
        "agent_tools": summary["agent_tools"],
        "shopify_capabilities": summary["shopify_capabilities"],
        "model_list": [m.label for m in list_models()],
        "brain": "Fable 5",
        "fully_active": enabled == len(plugins) and len(plugins) > 0,
    }


def render_activation(report: dict[str, Any]) -> str:
    """Menschenlesbarer Aktivierungsbericht (Deutsch)."""

    ok = "✅" if report["fully_active"] else "⚠️"
    lines = [
        "🟢 J.A.R.V.I.S. — Aktivierung",
        f"{ok} Plugins aktiv: {report['plugins_enabled']}/{report['plugins_total']}",
        f"🧠 Gehirn: {report['brain']}  ·  KI-Modelle: {report['models']} ({', '.join(report['model_list'])})",
        f"🛠️ Agent-Werkzeuge: {report['agent_tools']}  ·  🛒 Shopify-Faehigkeiten: {report['shopify_capabilities']}",
        f"📚 Skills: {report['skills']}  ·  🧩 Tools: {report['tools']}",
        "Status: " + ("ALLES AKTIV" if report["fully_active"] else "teilweise aktiv"),
    ]
    return "\n".join(lines)
