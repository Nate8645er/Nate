"""JARVIS Enterprise Plugin: Dependency-Radar (Kategorie: Entwicklung)."""

from __future__ import annotations

import json

PLUGIN_ID = "entwicklung_dependency_radar"
KATEGORIE = "Entwicklung"
BEFEHLE: list[str] = [
    "abhängigkeiten prüfen",
    "veraltete pakete anzeigen",
    "sicherheitslücken anzeigen",
    "update vorschlagen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
