"""JARVIS Enterprise Plugin: Navigations-Copilot (Kategorie: Reisen & Alltag)."""

from __future__ import annotations

import json

PLUGIN_ID = "reisen_alltag_navigations_copilot"
KATEGORIE = "Reisen & Alltag"
BEFEHLE: list[str] = [
    "route berechnen",
    "navigation starten",
    "verkehrslage anzeigen",
    "ankunftszeit anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
