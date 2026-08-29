"""JARVIS Enterprise Plugin: Google-Drive-Anschluss (Kategorie: Integrationen)."""

from __future__ import annotations

import json

PLUGIN_ID = "integrationen_google_drive_anschluss"
KATEGORIE = "Integrationen"
BEFEHLE: list[str] = [
    "datei suchen",
    "datei hochladen",
    "freigabe verwalten",
    "letzte dateien anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
