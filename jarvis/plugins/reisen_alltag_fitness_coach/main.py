"""JARVIS Enterprise Plugin: Fitness-Coach (Kategorie: Reisen & Alltag)."""

from __future__ import annotations

import json

PLUGIN_ID = "reisen_alltag_fitness_coach"
KATEGORIE = "Reisen & Alltag"
BEFEHLE: list[str] = [
    "training starten",
    "übung anzeigen",
    "fortschritt anzeigen",
    "trainingsplan erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
