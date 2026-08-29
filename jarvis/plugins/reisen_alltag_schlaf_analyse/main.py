"""JARVIS Enterprise Plugin: Schlaf-Analyse (Kategorie: Reisen & Alltag)."""

from __future__ import annotations

import json

PLUGIN_ID = "reisen_alltag_schlaf_analyse"
KATEGORIE = "Reisen & Alltag"
BEFEHLE: list[str] = [
    "schlaf auswerten",
    "schlafbericht anzeigen",
    "weckzeit empfehlen",
    "schlafziel setzen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
