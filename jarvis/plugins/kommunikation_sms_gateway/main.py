"""JARVIS Enterprise Plugin: SMS-Gateway (Kategorie: Kommunikation)."""

from __future__ import annotations

import json

PLUGIN_ID = "kommunikation_sms_gateway"
KATEGORIE = "Kommunikation"
BEFEHLE: list[str] = [
    "sms senden",
    "sms anzeigen",
    "sms vorlesen",
    "kontakt wählen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
