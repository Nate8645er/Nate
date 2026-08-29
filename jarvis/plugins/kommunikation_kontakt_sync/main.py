"""JARVIS Enterprise Plugin: Kontakt-Sync (Kategorie: Kommunikation)."""

from __future__ import annotations

import json

PLUGIN_ID = "kommunikation_kontakt_sync"
KATEGORIE = "Kommunikation"
BEFEHLE: list[str] = [
    "kontakte synchronisieren",
    "kontakt suchen",
    "duplikate bereinigen",
    "kontakt anlegen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
