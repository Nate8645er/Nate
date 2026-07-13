"""JARVIS-Agent Plugin-Entrypoint.

Meldet die Befehle des agentischen Modus. Die eigentliche Logik liegt in
open_jarvis.agent (CLI: python3 -m open_jarvis.agent "<befehl>").
"""

from __future__ import annotations

import json

PLUGIN_ID = "agent_jarvis_agent"
CATEGORY = "KI & Assistenz"
COMMANDS = [
    "agent starte <befehl>",
    "baue einen shop fuer <produkt>",
    "modell waehlen <fable-5|opus-4.8|local>",
    "agent modelle anzeigen",
    "agent ausfuehren <befehl>",
]


def register() -> dict:
    return {"id": PLUGIN_ID, "category": CATEGORY, "commands": COMMANDS}


if __name__ == "__main__":
    print(json.dumps(register(), ensure_ascii=False))
