"""JARVIS Enterprise Plugin: Netzwerk-Scanner (defensiv) (Kategorie: Sicherheit)."""

from __future__ import annotations

import json

PLUGIN_ID = "sicherheit_netzwerk_scanner_defensiv"
KATEGORIE = "Sicherheit"
BEFEHLE: list[str] = [
    "netzwerk scannen",
    "geräte auflisten",
    "offene ports anzeigen",
    "scanbericht erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
