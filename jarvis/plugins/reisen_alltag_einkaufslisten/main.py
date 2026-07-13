"""JARVIS Enterprise Plugin: Einkaufslisten (Kategorie: Reisen & Alltag)."""

from __future__ import annotations

import json

PLUGIN_ID = "reisen_alltag_einkaufslisten"
KATEGORIE = "Reisen & Alltag"
BEFEHLE: list[str] = [
    "artikel hinzufügen",
    "liste anzeigen",
    "artikel abhaken",
    "liste teilen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
