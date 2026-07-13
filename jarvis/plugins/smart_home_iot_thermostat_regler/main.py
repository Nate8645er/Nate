"""JARVIS Enterprise Plugin: Thermostat-Regler (Kategorie: Smart Home & IoT)."""

from __future__ import annotations

import json

PLUGIN_ID = "smart_home_iot_thermostat_regler"
KATEGORIE = "Smart Home & IoT"
BEFEHLE: list[str] = [
    "temperatur einstellen",
    "heizplan anzeigen",
    "eco-modus aktivieren",
    "temperatur anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
