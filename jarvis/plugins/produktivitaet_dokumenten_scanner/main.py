"""JARVIS Enterprise Plugin: Dokumenten-Scanner (Kategorie: Produktivitaet)."""

from __future__ import annotations

import json

PLUGIN_ID = "produktivitaet_dokumenten_scanner"
KATEGORIE = "Produktivitaet"
BEFEHLE: list[str] = [
    "dokument scannen",
    "text erkennen",
    "scan speichern",
    "scan benennen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
