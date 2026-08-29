"""JARVIS Enterprise Plugin: Org-Chart-Navigator (Kategorie: Enterprise)."""

from __future__ import annotations

import json

PLUGIN_ID = "enterprise_org_chart_navigator"
KATEGORIE = "Enterprise"
BEFEHLE: list[str] = [
    "organigramm anzeigen",
    "abteilung öffnen",
    "mitarbeiter suchen",
    "berichtslinie anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
