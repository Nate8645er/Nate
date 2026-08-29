"""JARVIS Enterprise Plugin: Gesetzes-Suche (Kategorie: Wissen & Recherche)."""

from __future__ import annotations

import json

PLUGIN_ID = "wissen_recherche_gesetzes_suche"
KATEGORIE = "Wissen & Recherche"
BEFEHLE: list[str] = [
    "gesetz suchen",
    "paragraph anzeigen",
    "änderungen anzeigen",
    "gesetz zusammenfassen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
