"""JARVIS Enterprise Plugin: Berechtigungs-Auditor (Kategorie: Sicherheit)."""

from __future__ import annotations

import json

PLUGIN_ID = "sicherheit_berechtigungs_auditor"
KATEGORIE = "Sicherheit"
BEFEHLE: list[str] = [
    "berechtigungen prüfen",
    "riskante rechte anzeigen",
    "auditbericht erstellen",
    "empfehlungen anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
