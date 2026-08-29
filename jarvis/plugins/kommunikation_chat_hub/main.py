"""JARVIS Enterprise Plugin: Chat-Hub (Kategorie: Kommunikation)."""

from __future__ import annotations

import json

PLUGIN_ID = "kommunikation_chat_hub"
KATEGORIE = "Kommunikation"
BEFEHLE: list[str] = [
    "nachricht senden",
    "chats anzeigen",
    "ungelesene anzeigen",
    "chat stummschalten",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
