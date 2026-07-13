"""JARVIS Enterprise Plugin: Wake-Word-Tuner (Kategorie: Sprache & Audio)."""

from __future__ import annotations

import json

PLUGIN_ID = "sprache_audio_wake_word_tuner"
KATEGORIE = "Sprache & Audio"
BEFEHLE: list[str] = [
    "wake-word testen",
    "empfindlichkeit einstellen",
    "wake-word wechseln",
    "erkennungsbericht anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
