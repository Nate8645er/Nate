"""JARVIS Enterprise Plugin: REST-Adapter (Kategorie: Integrationen)."""

from __future__ import annotations

import json

PLUGIN_ID = "integrationen_rest_adapter"
KATEGORIE = "Integrationen"
BEFEHLE: list[str] = [
    "endpunkt aufrufen",
    "endpunkte anzeigen",
    "antwort prüfen",
    "adapter konfigurieren",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
