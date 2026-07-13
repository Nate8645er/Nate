"""JARVIS Enterprise Plugin: Deploy-Pilot (Kategorie: Entwicklung)."""

from __future__ import annotations

import json

PLUGIN_ID = "entwicklung_deploy_pilot"
KATEGORIE = "Entwicklung"
BEFEHLE: list[str] = [
    "deployment starten",
    "deployment status",
    "rollback ausführen",
    "release-notizen erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
