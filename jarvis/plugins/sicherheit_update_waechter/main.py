"""JARVIS Enterprise Plugin: Update-Waechter (Kategorie: Sicherheit)."""

from __future__ import annotations

import json

PLUGIN_ID = "sicherheit_update_waechter"
KATEGORIE = "Sicherheit"
BEFEHLE: list[str] = [
    "updates prüfen",
    "updates anzeigen",
    "update planen",
    "updatebericht erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
