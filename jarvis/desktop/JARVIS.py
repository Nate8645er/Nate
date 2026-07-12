"""JARVIS Desktop — lokaler Mission-Control-Server mit Claude-Anbindung.

Startet einen FastAPI-Server auf http://127.0.0.1:8737, liefert das
Mission-Control-Dashboard aus und beantwortet /api/chat über die
Anthropic API (Standard: Claude Fable 5 mit Opus-4.8-Fallback).

Start:  python JARVIS.py   (oder Start-JARVIS.bat)
Konfig: ANTHROPIC_API_KEY (Pflicht), JARVIS_MODEL, JARVIS_PORT
"""

import os
import threading
import webbrowser
from pathlib import Path

import anthropic
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

MODEL = os.environ.get("JARVIS_MODEL", "claude-fable-5")
FALLBACK_MODEL = "claude-opus-4-8"
PORT = int(os.environ.get("JARVIS_PORT", "8737"))
HOST = "127.0.0.1"
BASE_DIR = Path(__file__).resolve().parent
MAX_HISTORY_TURNS = 40  # user+assistant Einträge, die im Kontext bleiben

SYSTEM_PROMPT = """Du bist JARVIS, der persönliche KI-Chef-Assistent von Nate.

Rolle: Chief of Staff einer virtuellen Konzern-Holding ("Nate Group").
Du bist kompetent, loyal, proaktiv und hast trockenen britischen Humor,
bleibst aber immer respektvoll und praezise.

Regeln:
- Antworte auf Deutsch (Schweizer Kontext), ausser der Nutzer wechselt die Sprache.
- Deine Antworten werden oft laut vorgelesen: halte sie kurz und gespraechstauglich
  (2-6 Saetze fuer normale Fragen). Keine Markdown-Formatierung, keine Listen mit
  Sonderzeichen - sprich in ganzen Saetzen. Nur bei ausdruecklich verlangten
  Detailauskuenften darfst du laenger werden.
- Sprich den Nutzer gelegentlich mit "Sir" an, wie es sich fuer JARVIS gehoert.
- Du laeufst als lokale Desktop-App ohne Zugriff auf Dateien oder Programme des PCs.
  Wenn der Nutzer echte PC-Steuerung will, verweise auf Claude Code / die Claude
  Desktop-App mit Computer Use.
- Sei ehrlich ueber deine Grenzen. Erfinde keine Fakten."""

app = FastAPI(title="JARVIS Desktop")
client = anthropic.Anthropic()
history: list[dict] = []
history_lock = threading.Lock()


class ChatRequest(BaseModel):
    message: str


def api_key_present() -> bool:
    return bool(
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    )


def build_messages() -> list[dict]:
    with history_lock:
        return list(history[-MAX_HISTORY_TURNS:])


def ask_claude(user_message: str) -> str:
    with history_lock:
        history.append({"role": "user", "content": user_message})

    system = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ]

    if MODEL.startswith("claude-fable"):
        # Fable 5: Thinking ist immer an (Parameter weglassen). Server-seitiger
        # Fallback auf Opus 4.8, falls die Sicherheitsklassifizierer ablehnen.
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-06-01"],
            fallbacks=[{"model": FALLBACK_MODEL}],
            system=system,
            messages=build_messages(),
        )
    else:
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=system,
            messages=build_messages(),
        )

    if response.stop_reason == "refusal":
        with history_lock:
            history.pop()  # abgelehnten Turn nicht im Verlauf behalten
        return (
            "Diese Anfrage kann ich leider nicht bearbeiten, Sir - "
            "sie wurde von den Sicherheitsrichtlinien abgelehnt."
        )

    text = "".join(block.text for block in response.content if block.type == "text")
    if not text:
        text = "Dazu habe ich gerade keine Antwort, Sir. Versuchen wir es anders?"

    with history_lock:
        history.append({"role": "assistant", "content": text})
    return text


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (BASE_DIR / "mission-control.html").read_text(encoding="utf-8")


@app.get("/api/status")
def status() -> dict:
    return {
        "ok": True,
        "model": MODEL,
        "fallback": FALLBACK_MODEL if MODEL.startswith("claude-fable") else None,
        "key_present": api_key_present(),
        "turns": len(history),
    }


@app.post("/api/reset")
def reset() -> dict:
    with history_lock:
        history.clear()
    return {"ok": True}


@app.post("/api/chat")
def chat(req: ChatRequest):
    message = req.message.strip()
    if not message:
        return JSONResponse({"error": "Leere Nachricht."}, status_code=400)
    if not api_key_present():
        return JSONResponse(
            {
                "error": (
                    "Kein API-Key gefunden. Bitte setzen: "
                    'setx ANTHROPIC_API_KEY "sk-ant-..." '
                    "- danach neues Terminal oeffnen und JARVIS neu starten."
                )
            },
            status_code=503,
        )
    try:
        return {"reply": ask_claude(message)}
    except anthropic.AuthenticationError:
        return JSONResponse(
            {"error": "API-Key ungueltig. Bitte Key pruefen und JARVIS neu starten."},
            status_code=401,
        )
    except anthropic.RateLimitError:
        return JSONResponse(
            {"error": "Rate-Limit erreicht. Bitte kurz warten und erneut versuchen."},
            status_code=429,
        )
    except anthropic.APIStatusError as e:
        return JSONResponse(
            {"error": f"API-Fehler ({e.status_code}). Bitte spaeter erneut versuchen."},
            status_code=502,
        )
    except anthropic.APIConnectionError:
        return JSONResponse(
            {"error": "Keine Verbindung zur Anthropic API. Internet pruefen."},
            status_code=502,
        )


def open_browser() -> None:
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    print(f"  JARVIS Desktop  ->  http://{HOST}:{PORT}")
    print(f"  Modell: {MODEL}" + ("  (Fallback: " + FALLBACK_MODEL + ")" if MODEL.startswith("claude-fable") else ""))
    if not api_key_present():
        print('  [!] Kein ANTHROPIC_API_KEY gesetzt - Chat zeigt Einrichtungshinweis.')
    threading.Timer(1.5, open_browser).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
