"""JARVIS Enterprise Plugin: Web-Recherche (Kategorie: Wissen & Recherche)."""

from __future__ import annotations

import json

PLUGIN_ID = "wissen_recherche_web_recherche"
KATEGORIE = "Wissen & Recherche"
BEFEHLE: list[str] = [
    "recherche starten",
    "quellen sammeln",
    "ergebnisse zusammenfassen",
    "rechercheprotokoll erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
