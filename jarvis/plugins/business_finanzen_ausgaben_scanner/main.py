"""JARVIS Enterprise Plugin: Ausgaben-Scanner (Kategorie: Business & Finanzen)."""

from __future__ import annotations

import json

PLUGIN_ID = "business_finanzen_ausgaben_scanner"
KATEGORIE = "Business & Finanzen"
BEFEHLE: list[str] = [
    "beleg scannen",
    "ausgabe erfassen",
    "monatsübersicht anzeigen",
    "kategorien auswerten",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
