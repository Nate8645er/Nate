"""JARVIS Enterprise Plugin: Schicht-Planer (Kategorie: Enterprise)."""

from __future__ import annotations

import json

PLUGIN_ID = "enterprise_schicht_planer"
KATEGORIE = "Enterprise"
BEFEHLE: list[str] = [
    "schichtplan anzeigen",
    "schicht zuweisen",
    "schicht tauschen",
    "planungsbericht erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
