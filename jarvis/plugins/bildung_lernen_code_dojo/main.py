"""JARVIS Enterprise Plugin: Code-Dojo (Kategorie: Bildung & Lernen)."""

from __future__ import annotations

import json

PLUGIN_ID = "bildung_lernen_code_dojo"
KATEGORIE = "Bildung & Lernen"
BEFEHLE: list[str] = [
    "kata starten",
    "lösung prüfen",
    "hinweis anzeigen",
    "dojo-fortschritt anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
