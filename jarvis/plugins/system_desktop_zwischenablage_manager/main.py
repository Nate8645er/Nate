"""JARVIS Enterprise Plugin: Zwischenablage-Manager (Kategorie: System & Desktop)."""

from __future__ import annotations

import json

PLUGIN_ID = "system_desktop_zwischenablage_manager"
KATEGORIE = "System & Desktop"
BEFEHLE: list[str] = [
    "zwischenablage anzeigen",
    "verlauf durchsuchen",
    "eintrag einfügen",
    "verlauf leeren",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
