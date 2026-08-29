"""JARVIS Enterprise Plugin: PDF-Werkstatt (Kategorie: Produktivitaet)."""

from __future__ import annotations

import json

PLUGIN_ID = "produktivitaet_pdf_werkstatt"
KATEGORIE = "Produktivitaet"
BEFEHLE: list[str] = [
    "pdf zusammenführen",
    "pdf teilen",
    "pdf komprimieren",
    "pdf unterschreiben",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
