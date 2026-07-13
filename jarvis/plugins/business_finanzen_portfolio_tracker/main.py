"""JARVIS Enterprise Plugin: Portfolio-Tracker (Kategorie: Business & Finanzen)."""

from __future__ import annotations

import json

PLUGIN_ID = "business_finanzen_portfolio_tracker"
KATEGORIE = "Business & Finanzen"
BEFEHLE: list[str] = [
    "portfolio anzeigen",
    "performance berechnen",
    "transaktion erfassen",
    "portfoliobericht erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
