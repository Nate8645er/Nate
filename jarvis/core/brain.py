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
# Fallback-Kette: wird das bevorzugte Modell vom Key abgelehnt (400/404), werden
# der Reihe nach breit verfügbare Modell-IDs probiert, bis eines antwortet.
FALLBACK_MODELS = ["claude-opus-4-8", "claude-sonnet-5", "claude-haiku-4-5-20251001",
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


def describe_image(image_b64: str, media_type: str, frage: str) -> str:
    """Bildschirm-/Bild-Verstehen: schickt ein Bild an das Modell und fragt danach."""
    if mode() == "offline":
        return ("[OFFLINE-Modus] Bildschirm-Analyse braucht Fable 5 (API-Key). "
                "FABLE 5 aktivieren, dann sieht und beschreibt JARVIS deinen Bildschirm.")
    system = ("Du bist JARVIS und beschreibst, was auf dem Bildschirm/Bild zu sehen ist. "
              "Antworte knapp und konkret auf Deutsch. Erfinde nichts, was nicht sichtbar ist.")
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": media_type,
                                     "data": image_b64}},
        {"type": "text", "text": frage or "Was ist auf dem Bildschirm zu sehen?"},
    ]
    global _active_model
    order = ([_active_model] if _active_model else []) + \
            [m for m in _candidates() if m != _active_model]
    last_err = None
    for model in order:
        payload = {"model": model, "max_tokens": 700, "system": system,
                   "messages": [{"role": "user", "content": content}]}
        req = urllib.request.Request(
            API_URL, data=json.dumps(payload).encode(),
            headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                     "anthropic-version": "2023-06-01", "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            _active_model = model
            return "".join(b.get("text", "") for b in data.get("content", []))
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", "ignore")
            except Exception:
                pass
            if e.code == 404 or "model" in body.lower():
                last_err = f"[Modell {model} abgelehnt: {e.code}]"
                continue
            return f"[Bild-Analyse-Fehler {e.code}] {e.reason}"
        except Exception as e:
            return f"[Bild-Analyse nicht erreichbar: {type(e).__name__}]"
    return last_err or "[Bild-Analyse: kein gültiges Modell]"


def _call_with_fallback(system: str, user: str, max_tokens: int = 600) -> str:
    """Ruft das Modell; wird eine Modell-ID abgelehnt (400/404), nächste probieren.

    Auth-/Kredit-/Rate-Fehler (401/403/429) werden NICHT umgangen — dagegen hilft
    kein anderes Modell, sie werden sofort gemeldet.
    """
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
            low = body.lower()
            # Key-/Guthaben-/Rate-Problem: kein anderes Modell hilft -> sofort melden.
            # Body an die Ausnahme hängen (e.read() ist danach leer).
            if e.code in (401, 403, 429) or "credit balance" in low or "billing" in low:
                e._jarvis_body = body      # type: ignore[attr-defined]
                raise
            # 400/404 o. Ä.: dieses Modell taugt (für diesen Key) nicht -> nächstes
            last_err = f"[Modell {model}: HTTP {e.code}] {body[:200]}"
            if _active_model == model:
                _active_model = None       # nicht an kaputtem Modell festhalten
            continue
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
        body = getattr(e, "_jarvis_body", "")
        if not body:
            try:
                body = e.read().decode("utf-8", "ignore")
            except Exception:
                pass
        if "credit balance" in body.lower() or "billing" in body.lower():
            return ("[Kein Guthaben] Dein Anthropic-Konto hat kein Guthaben mehr. "
                    "Bitte auf console.anthropic.com unter 'Plans & Billing' Guthaben "
                    "aufladen — danach antwortet Fable 5. (Alternativ ein OpenRouter-"
                    "Modell nutzen: z. B. 'modell gpt: ...')")
        reason = {401: "Key ungültig", 403: "Key nicht berechtigt",
                  429: "Rate-Limit / kein Guthaben"}.get(e.code, f"HTTP {e.code}")
        return f"[API-Fehler {e.code}: {reason}] {body[:250]}"
    except RuntimeError as e:      # alle Modelle abgelehnt — echten Grund zeigen
        return f"[Kein Modell nutzbar] {e}"
    except Exception as e:  # Netzwerk o. ä.: ehrlich melden statt erfinden
        return f"[API nicht erreichbar: {type(e).__name__}] Aufgabe nicht bearbeitet."
