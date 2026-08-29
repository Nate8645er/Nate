"""JARVIS Enterprise Plugin: Notion-Sync (Kategorie: Integrationen)."""

from __future__ import annotations

import json

PLUGIN_ID = "integrationen_notion_sync"
KATEGORIE = "Integrationen"
BEFEHLE: list[str] = [
    "seite synchronisieren",
    "seite erstellen",
    "datenbank abfragen",
    "sync status",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
