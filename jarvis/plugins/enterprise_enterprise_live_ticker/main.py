"""JARVIS Enterprise Plugin: Enterprise-Live-Ticker (Kategorie: Enterprise)."""

from __future__ import annotations

import json

PLUGIN_ID = "enterprise_enterprise_live_ticker"
KATEGORIE = "Enterprise"
BEFEHLE: list[str] = [
    "live-ticker starten",
    "live-ticker stoppen",
    "belegschaft anzeigen",
    "mitarbeiter nachschlagen",
    "ticker-bericht erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
