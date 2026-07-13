"""JARVIS Enterprise Plugin: Quiz-Meister (Kategorie: Bildung & Lernen)."""

from __future__ import annotations

import json

PLUGIN_ID = "bildung_lernen_quiz_meister"
KATEGORIE = "Bildung & Lernen"
BEFEHLE: list[str] = [
    "quiz starten",
    "frage vorlesen",
    "punktestand anzeigen",
    "quiz erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
