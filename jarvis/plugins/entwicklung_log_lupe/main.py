"""JARVIS Enterprise Plugin: Log-Lupe (Kategorie: Entwicklung)."""

from __future__ import annotations

import json

PLUGIN_ID = "entwicklung_log_lupe"
KATEGORIE = "Entwicklung"
BEFEHLE: list[str] = [
    "logs durchsuchen",
    "fehler anzeigen",
    "live-ansicht starten",
    "logmuster erkennen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
