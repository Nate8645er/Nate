"""Das Gehirn: bindet aktive Agenten an ein Claude-Modell (z. B. Fable 5).

Zwei Modi, ehrlich getrennt:
  - "api":     ANTHROPIC_API_KEY ist gesetzt -> echte Modell-Aufrufe.
               Jeder Aufruf kostet reales API-Guthaben; deshalb bekommen
               nur AKTIVE Agenten Modellzugriff, nie der ganze Adressraum.
  - "offline": kein Key -> deterministische, regelbasierte Antworten,
               klar als Offline-Modus gekennzeichnet. Das System bleibt
               dadurch ohne Kosten voll demonstrier- und testbar.

Modellwahl: JARVIS versucht das konfigurierte Modell (Standard claude-fable-5)
und fällt bei "model not found" automatisch auf bekannte, gültige Modell-IDs
zurück — der tatsächlich funktionierende Name wird gemerkt und gemeldet.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .identity import VirtualEmployee

PREFERRED_MODEL = os.environ.get("JARVIS_MODEL", "claude-fable-5")
# Fallback-Kette gültiger öffentlicher Modell-IDs, falls das bevorzugte abgelehnt wird.
FALLBACK_MODELS = ["claude-fable-5", "claude-opus-4-8", "claude-sonnet-5",
                   "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"]
API_URL = "https://api.anthropic.com/v1/messages"

# Das zuletzt als funktionierend bestätigte Modell (wird nach Verify/Antwort gesetzt).
DEFAULT_MODEL = PREFERRED_MODEL
_active_model: str | None = None


def mode() -> str:
    return "api" if os.environ.get("ANTHROPIC_API_KEY") else "offline"


def active_model() -> str:
    return _active_model or DEFAULT_MODEL


def _candidates() -> list[str]:
    seen, out = set(), []
    for m in [PREFERRED_MODEL, *FALLBACK_MODELS]:
        if m and m not in seen:
            seen.add(m); out.append(m)
    return out


def _call(model: str, system: str, user: str, max_tokens: int = 600) -> str:
    payload = {"model": model, "max_tokens": max_tokens,
               "system": system, "messages": [{"role": "user", "content": user}]}
    req = urllib.request.Request(
        API_URL, data=json.dumps(payload).encode(),
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return "".join(block.get("text", "") for block in data.get("content", []))


def _call_with_fallback(system: str, user: str, max_tokens: int = 600) -> str:
    """Ruft das Modell; bei 404/model-not-found nächste ID der Kette probieren."""
    global _active_model
    order = ([_active_model] if _active_model else []) + \
            [m for m in _candidates() if m != _active_model]
    last_err = None
    for model in order:
        try:
            text = _call(model, system, user, max_tokens)
            _active_model = model
            return text
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "ignore")
            except Exception:
                pass
            # Nur bei Modell-Problemen weiterprobieren; Auth-/Kredit-Fehler sofort melden.
            if e.code in (404,) or "model" in body.lower():
                last_err = f"[Modell {model} abgelehnt: {e.code}]"
                continue
            raise
    raise RuntimeError(last_err or "kein gültiges Modell gefunden")


def verify() -> dict:
    """Echter Mini-Testaufruf: prüft Key + Modell, ohne etwas zu erfinden."""
    if mode() == "offline":
        return {"ok": False, "modus": "offline", "grund": "kein API-Key gesetzt"}
    try:
        _call_with_fallback("Antworte mit genau einem Wort.", "Sag 'bereit'.", max_tokens=10)
        return {"ok": True, "modus": "api", "modell": active_model()}
    except urllib.error.HTTPError as e:
        reason = {401: "Key ungültig", 403: "Key nicht berechtigt",
                  429: "Rate-Limit / kein Guthaben"}.get(e.code, f"HTTP {e.code}")
        return {"ok": False, "modus": "api", "grund": reason}
    except Exception as e:
        return {"ok": False, "modus": "api", "grund": f"nicht erreichbar ({type(e).__name__})"}


def _offline_answer(employee: VirtualEmployee, task: str) -> str:
    return (
        f"[OFFLINE-Modus, kein API-Key] {employee.display} hat die Aufgabe "
        f"entgegengenommen und strukturiert: '{task[:120]}'. "
        f"Eingesetzte Skills: {', '.join(employee.skills[:2])}. "
        f"Für echte KI-Antworten Fable 5 aktivieren (API-Key setzen)."
    )


def answer(employee: VirtualEmployee, task: str) -> str:
    """Beantwortet eine Aufgabe im Namen eines aktiven Agenten."""
    if mode() == "offline":
        return _offline_answer(employee, task)
    system = (
        f"Du bist {employee.name}, {employee.role} im Team {employee.team} "
        f"einer virtuellen Organisation (JARVIS). Deine Skills: "
        f"{', '.join(employee.skills)}. Antworte knapp, präzise und auf Deutsch. "
        f"Erfinde keine Fakten und stelle keine simulierten Ergebnisse als real dar.")
    try:
        return _call_with_fallback(system, task)
    except urllib.error.HTTPError as e:
        return f"[API-Fehler {e.code}] {e.reason} — Aufgabe nicht bearbeitet."
    except Exception as e:  # Netzwerk o. ä.: ehrlich melden statt erfinden
        return f"[API nicht erreichbar: {type(e).__name__}] Aufgabe nicht bearbeitet."
