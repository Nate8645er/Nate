"""JARVIS Enterprise Plugin: Audio-Mixer (Kategorie: Sprache & Audio)."""

from __future__ import annotations

import json

PLUGIN_ID = "sprache_audio_audio_mixer"
KATEGORIE = "Sprache & Audio"
BEFEHLE: list[str] = [
    "lautstärke mischen",
    "quelle stummschalten",
    "profil speichern",
    "profil laden",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
