"""JARVIS Enterprise Plugin: Zitate-Archiv (Kategorie: Wissen & Recherche)."""

from __future__ import annotations

import json

PLUGIN_ID = "wissen_recherche_zitate_archiv"
KATEGORIE = "Wissen & Recherche"
BEFEHLE: list[str] = [
    "zitat des tages",
    "zitat suchen",
    "zitat speichern",
    "zitat teilen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
