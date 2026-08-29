"""JARVIS Enterprise Plugin: Datenschutz-Cockpit (Kategorie: Sicherheit)."""

from __future__ import annotations

import json

PLUGIN_ID = "sicherheit_datenschutz_cockpit"
KATEGORIE = "Sicherheit"
BEFEHLE: list[str] = [
    "datenschutz status",
    "tracker anzeigen",
    "daten löschen",
    "datenschutzbericht erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
