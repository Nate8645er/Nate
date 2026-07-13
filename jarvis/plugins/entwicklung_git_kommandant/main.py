"""JARVIS Enterprise Plugin: Git-Kommandant (Kategorie: Entwicklung)."""

from __future__ import annotations

import json

PLUGIN_ID = "entwicklung_git_kommandant"
KATEGORIE = "Entwicklung"
BEFEHLE: list[str] = [
    "status anzeigen",
    "änderungen anzeigen",
    "branch wechseln",
    "verlauf anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
