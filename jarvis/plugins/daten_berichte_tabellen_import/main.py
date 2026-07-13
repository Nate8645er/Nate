"""JARVIS Enterprise Plugin: Tabellen-Import (Kategorie: Daten & Berichte)."""

from __future__ import annotations

import json

PLUGIN_ID = "daten_berichte_tabellen_import"
KATEGORIE = "Daten & Berichte"
BEFEHLE: list[str] = [
    "tabelle importieren",
    "spalten zuordnen",
    "vorschau anzeigen",
    "import starten",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
