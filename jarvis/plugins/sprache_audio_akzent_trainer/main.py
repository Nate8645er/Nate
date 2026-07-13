"""JARVIS Enterprise Plugin: Akzent-Trainer (Kategorie: Sprache & Audio)."""

from __future__ import annotations

import json

PLUGIN_ID = "sprache_audio_akzent_trainer"
KATEGORIE = "Sprache & Audio"
BEFEHLE: list[str] = [
    "übung starten",
    "aussprache bewerten",
    "fortschritt anzeigen",
    "übungsplan erstellen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
