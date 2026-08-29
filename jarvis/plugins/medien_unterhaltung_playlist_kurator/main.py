"""JARVIS Enterprise Plugin: Playlist-Kurator (Kategorie: Medien & Unterhaltung)."""

from __future__ import annotations

import json

PLUGIN_ID = "medien_unterhaltung_playlist_kurator"
KATEGORIE = "Medien & Unterhaltung"
BEFEHLE: list[str] = [
    "playlist erstellen",
    "songs vorschlagen",
    "playlist mischen",
    "playlist teilen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
