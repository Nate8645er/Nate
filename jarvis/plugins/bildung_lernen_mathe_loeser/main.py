"""JARVIS Enterprise Plugin: Mathe-Loeser (Kategorie: Bildung & Lernen)."""

from __future__ import annotations

import json

PLUGIN_ID = "bildung_lernen_mathe_loeser"
KATEGORIE = "Bildung & Lernen"
BEFEHLE: list[str] = [
    "aufgabe lösen",
    "lösungsweg anzeigen",
    "formel erklären",
    "übungsaufgabe erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
