"""JARVIS Enterprise Plugin: Screenshot-Studio (Kategorie: System & Desktop)."""

from __future__ import annotations

import json

PLUGIN_ID = "system_desktop_screenshot_studio"
KATEGORIE = "System & Desktop"
BEFEHLE: list[str] = [
    "screenshot aufnehmen",
    "bereich aufnehmen",
    "screenshot kommentieren",
    "screenshot teilen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
