"""JARVIS Enterprise Plugin: Agenten-Fabrik (Kategorie: KI & Assistenz)."""

from __future__ import annotations

import json

PLUGIN_ID = "ki_assistenz_agenten_fabrik"
KATEGORIE = "KI & Assistenz"
BEFEHLE: list[str] = [
    "agent erstellen",
    "agent starten",
    "agenten anzeigen",
    "agent stoppen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
