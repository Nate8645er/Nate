"""JARVIS Enterprise Plugin: Report-Fabrik (Kategorie: Daten & Berichte)."""

from __future__ import annotations

import json

PLUGIN_ID = "daten_berichte_report_fabrik"
KATEGORIE = "Daten & Berichte"
BEFEHLE: list[str] = [
    "report erstellen",
    "vorlage wählen",
    "report planen",
    "report exportieren",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
