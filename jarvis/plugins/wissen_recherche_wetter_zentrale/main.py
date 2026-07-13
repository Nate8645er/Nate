"""JARVIS Enterprise Plugin: Wetter-Zentrale (Kategorie: Wissen & Recherche)."""

from __future__ import annotations

import json

PLUGIN_ID = "wissen_recherche_wetter_zentrale"
KATEGORIE = "Wissen & Recherche"
BEFEHLE: list[str] = [
    "wetter heute",
    "wettervorhersage anzeigen",
    "regenradar anzeigen",
    "unwetterwarnung aktivieren",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
