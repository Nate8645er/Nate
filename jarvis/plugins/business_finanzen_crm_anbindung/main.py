"""JARVIS Enterprise Plugin: CRM-Anbindung (Kategorie: Business & Finanzen)."""

from __future__ import annotations

import json

PLUGIN_ID = "business_finanzen_crm_anbindung"
KATEGORIE = "Business & Finanzen"
BEFEHLE: list[str] = [
    "kontakt anzeigen",
    "lead anlegen",
    "pipeline anzeigen",
    "aktivität protokollieren",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
