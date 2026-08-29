"""JARVIS Enterprise Plugin: Wissenschafts-Feed (Kategorie: Wissen & Recherche)."""

from __future__ import annotations

import json

PLUGIN_ID = "wissen_recherche_wissenschafts_feed"
KATEGORIE = "Wissen & Recherche"
BEFEHLE: list[str] = [
    "neue studien anzeigen",
    "thema abonnieren",
    "studie zusammenfassen",
    "feed vorlesen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
