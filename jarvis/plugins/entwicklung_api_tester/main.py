"""JARVIS Enterprise Plugin: API-Tester (Kategorie: Entwicklung)."""

from __future__ import annotations

import json

PLUGIN_ID = "entwicklung_api_tester"
KATEGORIE = "Entwicklung"
BEFEHLE: list[str] = [
    "anfrage senden",
    "sammlung ausführen",
    "antwort prüfen",
    "testbericht erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
