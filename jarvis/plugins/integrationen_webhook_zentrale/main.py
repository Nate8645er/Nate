"""JARVIS Enterprise Plugin: Webhook-Zentrale (Kategorie: Integrationen)."""

from __future__ import annotations

import json

PLUGIN_ID = "integrationen_webhook_zentrale"
KATEGORIE = "Integrationen"
BEFEHLE: list[str] = [
    "webhook registrieren",
    "webhooks anzeigen",
    "webhook testen",
    "webhook deaktivieren",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
