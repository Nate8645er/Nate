"""Das Gehirn: bindet aktive Agenten an ein Claude-Modell (z. B. Fable 5).

Zwei Modi, ehrlich getrennt:
  - "api":     ANTHROPIC_API_KEY ist gesetzt -> echte Modell-Aufrufe.
               Jeder Aufruf kostet reales API-Guthaben; deshalb bekommen
               nur AKTIVE Agenten Modellzugriff, nie der ganze Adressraum.
  - "offline": kein Key -> deterministische, regelbasierte Antworten,
               klar als Offline-Modus gekennzeichnet. Das System bleibt
               dadurch ohne Kosten voll demonstrier- und testbar.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .identity import VirtualEmployee

DEFAULT_MODEL = os.environ.get("JARVIS_MODEL", "claude-fable-5")
API_URL = "https://api.anthropic.com/v1/messages"


def mode() -> str:
    return "api" if os.environ.get("ANTHROPIC_API_KEY") else "offline"


def _offline_answer(employee: VirtualEmployee, task: str) -> str:
    return (
        f"[OFFLINE-Modus, kein API-Key] {employee.display} hat die Aufgabe "
        f"entgegengenommen und strukturiert: '{task[:120]}'. "
        f"Eingesetzte Skills: {', '.join(employee.skills[:2])}. "
        f"Für echte KI-Antworten ANTHROPIC_API_KEY setzen."
    )


def _api_answer(employee: VirtualEmployee, task: str) -> str:
    payload = {
        "model": DEFAULT_MODEL,
        "max_tokens": 600,
        "system": (
            f"Du bist {employee.name}, {employee.role} im Team {employee.team} "
            f"einer virtuellen Organisation (JARVIS). Deine Skills: "
            f"{', '.join(employee.skills)}. Antworte knapp, präzise und auf Deutsch. "
            f"Erfinde keine Fakten und stelle keine simulierten Ergebnisse als real dar."
        ),
        "messages": [{"role": "user", "content": task}],
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return "".join(block.get("text", "") for block in data.get("content", []))


def answer(employee: VirtualEmployee, task: str) -> str:
    """Beantwortet eine Aufgabe im Namen eines aktiven Agenten."""
    if mode() == "offline":
        return _offline_answer(employee, task)
    try:
        return _api_answer(employee, task)
    except urllib.error.HTTPError as e:
        return f"[API-Fehler {e.code}] {e.reason} — Aufgabe nicht bearbeitet."
    except Exception as e:  # Netzwerk o. ä.: ehrlich melden statt erfinden
        return f"[API nicht erreichbar: {type(e).__name__}] Aufgabe nicht bearbeitet."
