"""JARVIS Enterprise Plugin: Pomodoro-Coach (Kategorie: Produktivitaet)."""

from __future__ import annotations

import json

PLUGIN_ID = "produktivitaet_pomodoro_coach"
KATEGORIE = "Produktivitaet"
BEFEHLE: list[str] = [
    "pomodoro starten",
    "pause starten",
    "sitzung beenden",
    "fokus statistik",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
