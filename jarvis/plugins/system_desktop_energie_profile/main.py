"""JARVIS Enterprise Plugin: Energie-Profile (Kategorie: System & Desktop)."""

from __future__ import annotations

import json

PLUGIN_ID = "system_desktop_energie_profile"
KATEGORIE = "System & Desktop"
BEFEHLE: list[str] = [
    "energieprofil wechseln",
    "sparmodus aktivieren",
    "leistungsmodus aktivieren",
    "akku status",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
