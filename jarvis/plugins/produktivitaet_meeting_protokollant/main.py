"""JARVIS Enterprise Plugin: Meeting-Protokollant (Kategorie: Produktivitaet)."""

from __future__ import annotations

import json

PLUGIN_ID = "produktivitaet_meeting_protokollant"
KATEGORIE = "Produktivitaet"
BEFEHLE: list[str] = [
    "protokoll starten",
    "protokoll beenden",
    "zusammenfassung erstellen",
    "aufgaben extrahieren",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
