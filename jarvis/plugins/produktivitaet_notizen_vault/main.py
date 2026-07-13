"""JARVIS Enterprise Plugin: Notizen-Vault (Kategorie: Produktivitaet)."""

from __future__ import annotations

import json

PLUGIN_ID = "produktivitaet_notizen_vault"
KATEGORIE = "Produktivitaet"
BEFEHLE: list[str] = [
    "notiz erstellen",
    "notizen durchsuchen",
    "notiz vorlesen",
    "notiz verschlüsseln",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
