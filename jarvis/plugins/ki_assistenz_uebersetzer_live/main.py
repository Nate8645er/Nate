"""JARVIS Enterprise Plugin: Uebersetzer-Live (Kategorie: KI & Assistenz)."""

from __future__ import annotations

import json

PLUGIN_ID = "ki_assistenz_uebersetzer_live"
KATEGORIE = "KI & Assistenz"
BEFEHLE: list[str] = [
    "text übersetzen",
    "sprache erkennen",
    "live-übersetzung starten",
    "übersetzung vorlesen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
