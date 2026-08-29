"""JARVIS Enterprise Plugin: Flotten-Manager (Kategorie: Enterprise)."""

from __future__ import annotations

import json

PLUGIN_ID = "enterprise_flotten_manager"
KATEGORIE = "Enterprise"
BEFEHLE: list[str] = [
    "flotte anzeigen",
    "fahrzeugstatus prüfen",
    "wartung planen",
    "flottenbericht erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
