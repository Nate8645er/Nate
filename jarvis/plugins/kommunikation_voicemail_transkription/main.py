"""JARVIS Enterprise Plugin: Voicemail-Transkription (Kategorie: Kommunikation)."""

from __future__ import annotations

import json

PLUGIN_ID = "kommunikation_voicemail_transkription"
KATEGORIE = "Kommunikation"
BEFEHLE: list[str] = [
    "voicemail transkribieren",
    "transkripte anzeigen",
    "voicemail vorlesen",
    "transkript teilen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
