"""JARVIS Enterprise Plugin: System-Monitor (Kategorie: System & Desktop)."""

from __future__ import annotations

import json

PLUGIN_ID = "system_desktop_system_monitor"
KATEGORIE = "System & Desktop"
BEFEHLE: list[str] = [
    "systemauslastung anzeigen",
    "cpu status",
    "arbeitsspeicher prüfen",
    "systembericht erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
