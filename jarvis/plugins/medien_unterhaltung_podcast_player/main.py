"""JARVIS Enterprise Plugin: Podcast-Player (Kategorie: Medien & Unterhaltung)."""

from __future__ import annotations

import json

PLUGIN_ID = "medien_unterhaltung_podcast_player"
KATEGORIE = "Medien & Unterhaltung"
BEFEHLE: list[str] = [
    "podcast abspielen",
    "folge fortsetzen",
    "abo verwalten",
    "neue folgen anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
