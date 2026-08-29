"""JARVIS Enterprise Plugin: E-Mail-Assistent (Kategorie: Produktivitaet)."""

from __future__ import annotations

import json

PLUGIN_ID = "produktivitaet_e_mail_assistent"
KATEGORIE = "Produktivitaet"
BEFEHLE: list[str] = [
    "posteingang zusammenfassen",
    "e-mail verfassen",
    "e-mail beantworten",
    "wichtige mails anzeigen",
]


def plugin_info() -> dict[str, object]:
    """Liefert die Plugin-Metadaten fuer den JARVIS Befehls-Katalog."""

    return {"plugin_id": PLUGIN_ID, "kategorie": KATEGORIE, "befehle": BEFEHLE}


if __name__ == "__main__":
    print(json.dumps(plugin_info(), ensure_ascii=False))
