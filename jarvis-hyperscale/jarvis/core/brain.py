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

# Boss/Worker-Aufteilung (Nates Setup): Fable 5 orchestriert und führt zusammen,
# GPT-5.6 Sol Ultra erledigt die eigentliche Mitarbeiter-Arbeit. Der Worker
# läuft über OpenRouter (openai/gpt-5.6-sol-ultra) — genau EIN OpenRouter-Key
# deckt damit Boss UND Worker ab. Ohne OpenRouter-Key fällt der Worker still
# auf das Boss-Gehirn (Fable 5) zurück; JARVIS bleibt in jedem Fall funktionsfähig.
# Beides per Umgebungsvariable überschreibbar; JARVIS_WORKER_MODEL=off schaltet
# die Aufteilung ab (dann macht Fable 5 alles).
BOSS_MODEL = os.environ.get("JARVIS_BOSS_MODEL", "").strip() or "claude-fable-5"
WORKER_MODEL = os.environ.get("JARVIS_WORKER_MODEL", "").strip() or "openai/gpt-5.6-sol-ultra"
# Direkter OpenAI-Weg für den Worker: greift, wenn ein OPENAI_API_KEY gesetzt
# ist, aber KEIN OpenRouter-Key — dann spricht JARVIS Sol Ultra direkt bei
# OpenAI an (ohne den 'openai/'-Präfix von OpenRouter).
OPENAI_WORKER_MODEL = os.environ.get("JARVIS_OPENAI_MODEL", "").strip() or "gpt-5.6-sol-ultra"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
_last_worker_model: str | None = None
# Fallback-Kette: wird das bevorzugte Modell vom Key abgelehnt (400/404), werden
# der Reihe nach breit verfügbare Modell-IDs probiert, bis eines antwortet.
FALLBACK_MODELS = ["claude-opus-4-8", "claude-sonnet-5", "claude-haiku-4-5-20251001",
                   "claude-3-5-sonnet-latest", "claude-3-5-haiku-latest"]
API_URL = "https://api.anthropic.com/v1/messages"

# OpenRouter-Gehirn: kostenlose Modelle zuerst (rate-limitiert, aber gratis).
# Über JARVIS_OPENROUTER_MODEL überschreibbar. IDs können sich ändern — bei
# Ablehnung wird das nächste probiert, sonst ehrliche Meldung.
OPENROUTER_FREE_MODELS = [
    "deepseek/deepseek-chat-v3-0324:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
]

# Das zuletzt als funktionierend bestätigte Modell (wird nach Verify/Antwort gesetzt).
DEFAULT_MODEL = PREFERRED_MODEL
_active_model: str | None = None
# Sobald Anthropic einmal an Guthaben/Auth scheitert, wird Fable 5 für diese
# Sitzung übersprungen (keine wiederholten Fehlermeldungen) -> direkt OpenRouter.
_skip_anthropic = False


def _only_openrouter() -> bool:
    """Fable 5 komplett überspringen? (JARVIS_BRAIN=openrouter oder nach Guthaben-Fehler)"""
    if os.environ.get("JARVIS_BRAIN", "").lower() == "openrouter":
        return True
    return _skip_anthropic


def mode() -> str:
    """api, sobald irgendein Modell-Zugang da ist (Anthropic ODER OpenRouter ODER OpenAI)."""
    if (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("OPENAI_API_KEY")):
        return "api"
    return "offline"


def _openrouter_answer(system: str, user: str, max_tokens: int = 600) -> str | None:
    """Antwort über OpenRouter-Gratis-Modelle (mit Fallback). None = kein Erfolg."""
    from . import openrouter
    global _active_model
    if not openrouter.available():
        return None
    pref = os.environ.get("JARVIS_OPENROUTER_MODEL", "").strip()
    order = ([pref] if pref else []) + [m for m in OPENROUTER_FREE_MODELS if m != pref]
    last = ""
    for m in order:
        r = openrouter.ask(m, user, system=system, max_tokens=max_tokens)
        if r and not r.startswith("[OpenRouter") and not r.startswith("[kein"):
            _active_model = m
            return r
        last = r or ""
    return f"[OpenRouter: kein Gratis-Modell verfügbar gerade] {last[:150]}"


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


def _build_system(employee: VirtualEmployee) -> str:
    return (
        f"Du bist {employee.name}, {employee.role} im Team {employee.team} "
        f"einer virtuellen Organisation (JARVIS). Deine Skills: "
        f"{', '.join(employee.skills)}. Antworte knapp, präzise und auf Deutsch. "
        f"Erfinde keine Fakten und stelle keine simulierten Ergebnisse als real dar. "
        f"WICHTIG zu deinen Fähigkeiten: JARVIS KANN den PC steuern — Programme und "
        f"Webseiten öffnen, den Browser bedienen, YouTube-Videos abspielen, "
        f"sich mit hinterlegten Zugangsdaten auf Plattformen EINLOGGEN, "
        f"Screenshots machen und im Internet suchen. Das geschieht über Befehle. "
        f"Behaupte NIEMALS, du hättest keinen Browser-/PC-Zugriff. Wenn der Nutzer "
        f"eine Aktion will (z. B. ein Video abspielen), sag ihm den kurzen Befehl, "
        f"der es auslöst — etwa: »spiel <Titel> auf YouTube« oder »öffne YouTube«. "
        f"Solche Sätze führt JARVIS wirklich aus.")


def _openai_configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def worker_model() -> str:
    """Modell-ID der Worker-Agenten (Sol Ultra) — Anzeige inkl. Transportweg."""
    from . import openrouter
    if bool(WORKER_MODEL) and WORKER_MODEL.lower() != "off":
        if openrouter.available():
            return WORKER_MODEL
        if _openai_configured():
            return f"{OPENAI_WORKER_MODEL} (OpenAI direkt)"
    return WORKER_MODEL


def boss_model() -> str:
    """Aktives Boss-Modell. Fable 5, sobald Anthropic/OpenRouter erreichbar; nur mit
    OpenAI-Key (kein Fable-Zugang) läuft auch der Boss ehrlich auf Sol."""
    from . import openrouter
    if os.environ.get("ANTHROPIC_API_KEY") or openrouter.available():
        return active_model()
    if _openai_configured():
        return f"{OPENAI_WORKER_MODEL} (OpenAI — kein Fable-Zugang)"
    return active_model()


def worker_active() -> bool:
    """Läuft die Worker-Arbeit wirklich auf Sol Ultra? Braucht einen Worker-Transport
    (OpenRouter ODER OpenAI-Key) und ein gesetztes Worker-Modell (nicht 'off')."""
    from . import openrouter
    if not WORKER_MODEL or WORKER_MODEL.lower() == "off":
        return False
    return openrouter.available() or _openai_configured()


def _openai_worker(system: str, task: str, max_tokens: int = 900) -> str | None:
    """Worker direkt über die OpenAI-API (Sol Ultra). None = Fehler/kein Key."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    payload = {"model": OPENAI_WORKER_MODEL,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": task}],
               "max_completion_tokens": max_tokens}
    req = urllib.request.Request(
        OPENAI_URL, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        text = (data["choices"][0]["message"]["content"] or "").strip()
        return text or None
    except Exception:      # Netz/Auth/Modell -> ehrlicher Rückfall aufs Boss-Gehirn
        return None


def _worker_answer(system: str, task: str) -> str | None:
    """Worker-Gehirn: GPT-5.6 Sol Ultra. Zuerst über OpenRouter (ein Key deckt Boss
    und Worker), sonst direkt über OpenAI. None = nicht verfügbar/Fehler (dann
    übernimmt das Boss-Gehirn/Fable 5 als ehrlicher Rückfall)."""
    if not worker_active():
        return None
    from . import openrouter
    global _last_worker_model
    if openrouter.available():
        r = openrouter.ask(WORKER_MODEL, task, system=system, max_tokens=900)
        if r and not r.startswith("[OpenRouter") and not r.startswith("[kein"):
            _last_worker_model = WORKER_MODEL
            return r
    if _openai_configured():
        r = _openai_worker(system, task)
        if r:
            _last_worker_model = OPENAI_WORKER_MODEL
            return r
    return None


def answer(employee: VirtualEmployee, task: str, role: str = "boss") -> str:
    """Beantwortet eine Aufgabe im Namen eines aktiven Agenten.

    role="worker": erledigende Mitarbeiter -> GPT-5.6 Sol Ultra (OpenRouter),
      bei fehlendem Key/Fehler Rückfall auf das Boss-Gehirn.
    role="boss" (Standard): Orchestrierung/Zusammenführung -> Fable 5. Reihenfolge:
      Anthropic (Fable 5) zuerst, falls Key + Guthaben vorhanden. Scheitert das an
      Guthaben/Auth, automatisch OpenRouter-Gratis-Modelle (falls Key). Sobald
      Anthropic wieder Guthaben hat, nutzt JARVIS von selbst wieder Fable 5.
    """
    if mode() == "offline":
        return _offline_answer(employee, task)
    system = _build_system(employee)
    if role == "worker":
        w = _worker_answer(system, task)
        if w is not None:
            return w
        # Kein OpenRouter/Sol -> Boss-Gehirn (Fable 5) als Rückfall.
    return _boss_brain(system, task)


def _boss_brain(system: str, task: str) -> str:
    global _skip_anthropic
    # 1) Anthropic (Fable 5) — nur wenn Key da UND nicht auf OpenRouter-only gestellt.
    if os.environ.get("ANTHROPIC_API_KEY") and not _only_openrouter():
        try:
            return _call_with_fallback(system, task)
        except urllib.error.HTTPError as e:
            body = getattr(e, "_jarvis_body", "")
            if not body:
                try:
                    body = e.read().decode("utf-8", "ignore")
                except Exception:
                    pass
            low = body.lower()
            billing = "credit balance" in low or "billing" in low
            # Bei Guthaben-/Auth-Problem: Fable 5 ab jetzt überspringen -> OpenRouter.
            if billing or e.code in (401, 403, 429):
                _skip_anthropic = True
                if os.environ.get("OPENROUTER_API_KEY"):
                    orr = _openrouter_answer(system, task)
                    if orr and not orr.startswith("[OpenRouter"):
                        return orr
                    # OpenRouter-Key da, aber Gratis-Modelle scheitern -> echten Grund zeigen
                    return ("[Anthropic kein Guthaben; OpenRouter-Gratis antwortet gerade "
                            "nicht] " + (orr or "unbekannt")[:200] +
                            " — evtl. Gratis-Limit erreicht (kurz warten) oder OpenRouter-"
                            "Key prüfen.")
                if billing:
                    return ("[Kein Guthaben] Dein Anthropic-Konto hat kein Guthaben und es "
                            "ist KEIN OpenRouter-Key gesetzt. Entweder auf "
                            "console.anthropic.com aufladen ODER auf der Werkzeuge-Seite "
                            "den OpenRouter-Key eintragen (Gratis-Modelle).")
            reason = {401: "Key ungültig", 403: "Key nicht berechtigt",
                      429: "Rate-Limit / kein Guthaben"}.get(e.code, f"HTTP {e.code}")
            return f"[API-Fehler {e.code}: {reason}] {body[:250]}"
        except RuntimeError:
            pass          # alle Anthropic-Modelle abgelehnt -> OpenRouter versuchen
        except Exception as e:
            return f"[API nicht erreichbar: {type(e).__name__}] Aufgabe nicht bearbeitet."

    # 2) OpenRouter-Gratis-Modelle (Standard, wenn kein Anthropic-Guthaben/-Key).
    orr = _openrouter_answer(system, task)
    if orr is not None:
        return orr
    # 3) Nur OpenAI-Key vorhanden: mangels Fable-Zugang läuft auch der Boss auf Sol.
    oa = _openai_worker(system, task)
    if oa is not None:
        return oa
    return ("[Kein Modell verfügbar] Weder Anthropic (Fable 5) noch OpenRouter "
            "noch OpenAI lieferten eine Antwort. Bitte Key/Guthaben prüfen.")
