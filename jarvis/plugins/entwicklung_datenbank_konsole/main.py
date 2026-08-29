"""JARVIS Enterprise Plugin: Datenbank-Konsole (Kategorie: Entwicklung)."""

from __future__ import annotations

import json

PLUGIN_ID = "entwicklung_datenbank_konsole"
KATEGORIE = "Entwicklung"
BEFEHLE: list[str] = [
    "abfrage ausführen",
    "tabellen anzeigen",
    "schema anzeigen",
    "verbindung prüfen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
