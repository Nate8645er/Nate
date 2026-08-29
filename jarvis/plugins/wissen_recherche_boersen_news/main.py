"""JARVIS Enterprise Plugin: Boersen-News (Kategorie: Wissen & Recherche)."""

from __future__ import annotations

import json

PLUGIN_ID = "wissen_recherche_boersen_news"
KATEGORIE = "Wissen & Recherche"
BEFEHLE: list[str] = [
    "marktnachrichten anzeigen",
    "aktien-news suchen",
    "news zusammenfassen",
    "newsalarm setzen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
