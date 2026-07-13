"""JARVIS Enterprise Plugin: Licht-Steuerung (Kategorie: Smart Home & IoT)."""

from __future__ import annotations

import json

PLUGIN_ID = "smart_home_iot_licht_steuerung"
KATEGORIE = "Smart Home & IoT"
BEFEHLE: list[str] = [
    "licht einschalten",
    "licht ausschalten",
    "helligkeit ändern",
    "lichtszene wählen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
