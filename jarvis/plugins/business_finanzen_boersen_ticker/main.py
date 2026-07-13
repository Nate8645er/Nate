"""JARVIS Enterprise Plugin: Boersen-Ticker (Kategorie: Business & Finanzen)."""

from __future__ import annotations

import json

PLUGIN_ID = "business_finanzen_boersen_ticker"
KATEGORIE = "Business & Finanzen"
BEFEHLE: list[str] = [
    "kurse anzeigen",
    "aktie suchen",
    "watchlist anzeigen",
    "kursalarm setzen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
