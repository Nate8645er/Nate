"""JARVIS Enterprise Plugin: Container-Deck (Kategorie: Entwicklung)."""

from __future__ import annotations

import json

PLUGIN_ID = "entwicklung_container_deck"
KATEGORIE = "Entwicklung"
BEFEHLE: list[str] = [
    "container auflisten",
    "container starten",
    "container stoppen",
    "logs anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
