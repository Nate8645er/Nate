"""JARVIS Enterprise Plugin: Geraeusch-Filter (Kategorie: Sprache & Audio)."""

from __future__ import annotations

import json

PLUGIN_ID = "sprache_audio_geraeusch_filter"
KATEGORIE = "Sprache & Audio"
BEFEHLE: list[str] = [
    "filter aktivieren",
    "filter deaktivieren",
    "filterstärke einstellen",
    "filtertest starten",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
