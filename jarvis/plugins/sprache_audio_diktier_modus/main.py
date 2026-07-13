"""JARVIS Enterprise Plugin: Diktier-Modus (Kategorie: Sprache & Audio)."""

from __future__ import annotations

import json

PLUGIN_ID = "sprache_audio_diktier_modus"
KATEGORIE = "Sprache & Audio"
BEFEHLE: list[str] = [
    "diktat starten",
    "diktat beenden",
    "text einfügen",
    "diktat korrigieren",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
