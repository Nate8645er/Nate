"""JARVIS Enterprise Plugin: Export-Zentrale (Kategorie: Daten & Berichte)."""

from __future__ import annotations

import json

PLUGIN_ID = "daten_berichte_export_zentrale"
KATEGORIE = "Daten & Berichte"
BEFEHLE: list[str] = [
    "export starten",
    "format wählen",
    "exporte anzeigen",
    "export planen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
