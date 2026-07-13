"""JARVIS Enterprise Plugin: Fenster-Organizer (Kategorie: System & Desktop)."""

from __future__ import annotations

import json

PLUGIN_ID = "system_desktop_fenster_organizer"
KATEGORIE = "System & Desktop"
BEFEHLE: list[str] = [
    "fenster anordnen",
    "layout speichern",
    "layout laden",
    "fenster fokussieren",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
