"""JARVIS Enterprise Plugin: Backup-Kommandant (Kategorie: Sicherheit)."""

from __future__ import annotations

import json

PLUGIN_ID = "sicherheit_backup_kommandant"
KATEGORIE = "Sicherheit"
BEFEHLE: list[str] = [
    "backup starten",
    "backup status",
    "wiederherstellung starten",
    "backup planen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
