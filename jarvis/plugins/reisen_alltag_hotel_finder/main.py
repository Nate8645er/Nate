"""JARVIS Enterprise Plugin: Hotel-Finder (Kategorie: Reisen & Alltag)."""

from __future__ import annotations

import json

PLUGIN_ID = "reisen_alltag_hotel_finder"
KATEGORIE = "Reisen & Alltag"
BEFEHLE: list[str] = [
    "hotel suchen",
    "preise vergleichen",
    "bewertungen anzeigen",
    "hotel merken",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
