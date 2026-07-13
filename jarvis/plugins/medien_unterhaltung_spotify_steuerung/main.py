"""JARVIS Enterprise Plugin: Spotify-Steuerung (Kategorie: Medien & Unterhaltung)."""

from __future__ import annotations

import json

PLUGIN_ID = "medien_unterhaltung_spotify_steuerung"
KATEGORIE = "Medien & Unterhaltung"
BEFEHLE: list[str] = [
    "musik abspielen",
    "musik pausieren",
    "nächster titel",
    "lautstärke ändern",
    "playlist starten",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
