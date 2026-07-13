"""JARVIS Enterprise Plugin: Szenen-Automatik (Kategorie: Smart Home & IoT)."""

from __future__ import annotations

import json

PLUGIN_ID = "smart_home_iot_szenen_automatik"
KATEGORIE = "Smart Home & IoT"
BEFEHLE: list[str] = [
    "szene aktivieren",
    "szene erstellen",
    "szenen anzeigen",
    "szene planen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
