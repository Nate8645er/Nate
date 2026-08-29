"""JARVIS Enterprise Plugin: Studienplaner (Kategorie: Bildung & Lernen)."""

from __future__ import annotations

import json

PLUGIN_ID = "bildung_lernen_studienplaner"
KATEGORIE = "Bildung & Lernen"
BEFEHLE: list[str] = [
    "lernplan erstellen",
    "prüfungen anzeigen",
    "lerneinheit planen",
    "studienfortschritt anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
