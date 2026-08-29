"""JARVIS Enterprise Plugin: Bahn-Auskunft (Kategorie: Reisen & Alltag)."""

from __future__ import annotations

import json

PLUGIN_ID = "reisen_alltag_bahn_auskunft"
KATEGORIE = "Reisen & Alltag"
BEFEHLE: list[str] = [
    "verbindung suchen",
    "verspätung prüfen",
    "abfahrten anzeigen",
    "ticketpreis anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
