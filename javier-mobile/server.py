# JAVIER MOBILE - FastAPI backend with Anthropic tool-use agent loop.
# Run via start.bat or: python server.py

import json
import os
import secrets
import socket
import sys

from dotenv import load_dotenv

load_dotenv()  # before importing tools (Shopify/IG creds)

import anthropic
import requests as http_requests
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import tools

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
CERT_FILE = os.path.join(BASE_DIR, "certs", "cert.pem")
KEY_FILE = os.path.join(BASE_DIR, "certs", "key.pem")

MODEL = "claude-fable-5"
MAX_AGENT_TURNS = 8

SYSTEM_PROMPT = """Du bist JAVIER, Nates persoenliche KI im Stil von JARVIS \
aus Iron Man: ruhig, praezise, trocken-hoeflich, niemals geschwaetzig. Du \
sprichst Hochdeutsch und nennst Nate beim Namen. Deine Antworten werden per \
Sprachsynthese vorgelesen - halte sie kurz, klar und gut sprechbar. Keine \
Markdown-Formatierung, keine Aufzaehlungszeichen, keine Emojis.

Du bist ein Agent: Nutze deine Tools selbststaendig, wenn sie die Anfrage \
beantworten (Todos, Kalender, Wetter Rapperswil-Jona, Shopify-Status von \
MeowUfo, Nachrichten vorbereiten, Instagram-Posts, Apps und Webseiten auf \
dem iPhone oeffnen, PC-Aktionen). Wenn Nate eine App oeffnen will (YouTube, \
Snapchat, Spotify usw.), nutze open_app - er bekommt dann einen Button.

Eiserne Regel fuer irreversible Aktionen: Bevor du prepare_message oder \
publish_instagram_post aufrufst, nenne Nate den genauen Inhalt und frage \
explizit um Bestaetigung, etwa: 'Soll ich das absenden, Nate?'. Rufe das \
Tool erst auf, nachdem Nate in seiner naechsten Nachricht zugestimmt hat.

Sei ehrlich ueber deine Grenzen: Du kannst auf dem iPhone keine Nachrichten \
vollautomatisch senden - du bereitest sie vor und Nate tippt auf Senden. \
Du hoerst nicht im Hintergrund mit; Nate muss den Sprechknopf druecken."""


app = FastAPI(title="JAVIER MOBILE")


@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    return resp


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class TTSRequest(BaseModel):
    text: str


def get_client():
    return anthropic.Anthropic()


def _check_password(request):
    password = os.environ.get("JAVIER_PASSWORD", "")
    if not password:
        # Cloud deployments (PORT is set by the host) must never run open:
        # without a shared secret the API would be public on Nate's keys.
        if "PORT" in os.environ:
            return JSONResponse({"error": "JAVIER_PASSWORD not set"},
                                status_code=401)
        return None
    supplied = request.headers.get("x-javier-key", "")
    if not secrets.compare_digest(supplied, password):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return None


def elevenlabs_configured():
    return bool(os.environ.get("ELEVENLABS_API_KEY")) and \
        bool(os.environ.get("ELEVENLABS_VOICE_ID"))


@app.post("/api/chat")
def chat(req: ChatRequest, request: Request):
    # Optional shared secret for public (cloud) deployments: if
    # JAVIER_PASSWORD is set, the frontend must send it along - otherwise
    # anyone with the URL could chat on Nate's API key.
    denied = _check_password(request)
    if denied:
        return denied
    client = get_client()
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    frontend_actions = []
    reply_text = ""

    for turn in range(MAX_AGENT_TURNS + 1):
        # Last turn: tool use forbidden, so the model must produce a
        # closing answer even if it would rather keep calling tools.
        # (Tool definitions stay in the request - the API requires them
        # whenever the history contains tool_use blocks.)
        final_turn = turn == MAX_AGENT_TURNS
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=tools.tool_definitions(),
                tool_choice={"type": "none"} if final_turn
                else {"type": "auto"},
                messages=messages,
            )
        except anthropic.APIConnectionError:
            return {"reply": "Entschuldige Nate, ich erreiche die "
                             "KI-Schnittstelle gerade nicht. Versuch es "
                             "gleich nochmal.",
                    "actions": frontend_actions}
        except anthropic.APIStatusError as e:
            return {"reply": "Entschuldige Nate, die KI-Schnittstelle "
                             "meldet Fehler %s. Versuch es gleich nochmal."
                             % e.status_code,
                    "actions": frontend_actions}
        text_parts = [b.text for b in response.content if b.type == "text"]
        if text_parts:
            reply_text = "\n".join(text_parts).strip()

        if final_turn or response.stop_reason != "tool_use":
            break

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = tools.execute_tool(block.name, block.input)
            action = result.pop("_frontend_action", None) \
                if isinstance(result, dict) else None
            if action:
                frontend_actions.append(action)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False),
            })
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return {"reply": reply_text or "Entschuldige Nate, da ist etwas "
                                   "schiefgelaufen.",
            "actions": frontend_actions}


@app.get("/api/health")
def health():
    return {"ok": True, "model": MODEL,
            "server_tts": elevenlabs_configured()}


@app.post("/api/tts")
def tts(req: TTSRequest, request: Request):
    # Custom AI voice via ElevenLabs - only active when
    # ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID are set. The frontend
    # falls back to the device voice if this endpoint is unavailable.
    denied = _check_password(request)
    if denied:
        return denied
    if not elevenlabs_configured():
        return JSONResponse({"error": "elevenlabs not configured"},
                            status_code=501)
    text = (req.text or "").strip()[:1500]
    if not text:
        return JSONResponse({"error": "text required"}, status_code=400)
    try:
        r = http_requests.post(
            "https://api.elevenlabs.io/v1/text-to-speech/%s"
            % os.environ["ELEVENLABS_VOICE_ID"],
            headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"],
                     "Content-Type": "application/json"},
            json={"text": text, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.5,
                                     "similarity_boost": 0.75}},
            timeout=30)
        r.raise_for_status()
    except http_requests.RequestException as e:
        return JSONResponse({"error": "elevenlabs failed: %s" % e},
                            status_code=502)
    return Response(content=r.content, media_type="audio/mpeg")


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def ensure_api_key():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    if not sys.stdin or not sys.stdin.isatty():
        # Cloud/headless start: no terminal to ask on.
        print("ANTHROPIC_API_KEY fehlt - als Umgebungsvariable setzen.")
        sys.exit(1)
    print("Kein ANTHROPIC_API_KEY in .env gefunden.")
    key = input("Bitte API-Key eingeben (sk-ant-...): ").strip()
    if not key:
        print("Ohne API-Key kann JAVIER nicht starten.")
        sys.exit(1)
    os.environ["ANTHROPIC_API_KEY"] = key
    save = input("In .env speichern? [j/N] ").strip().lower()
    if save == "j":
        with open(os.path.join(BASE_DIR, ".env"), "a", encoding="utf-8") as f:
            f.write("\nANTHROPIC_API_KEY=%s\n" % key)
        print("Gespeichert.")


def print_banner(https):
    ip = local_ip()
    scheme = "https" if https else "http"
    url = "%s://%s:8000" % (scheme, ip)
    print()
    print("=" * 52)
    print("  JAVIER MOBILE ist bereit.")
    print("  Auf dem iPhone oeffnen:  %s" % url)
    print("=" * 52)
    if not https:
        print("  WARNUNG: kein HTTPS-Zertifikat gefunden (certs/).")
        print("  iOS blockiert das Mikrofon ohne HTTPS!")
        print("  Siehe README.md, Abschnitt 'HTTPS mit mkcert'.")
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.print_ascii(invert=True)
    except ImportError:
        print("  (qrcode nicht installiert - kein QR-Code)")
    print()


if __name__ == "__main__":
    ensure_api_key()
    # Cloud hosts (e.g. Render) inject PORT and terminate TLS themselves.
    port = int(os.environ.get("PORT", "8000"))
    cloud = "PORT" in os.environ
    https = os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE)
    if cloud:
        if not os.environ.get("JAVIER_PASSWORD"):
            print("JAVIER_PASSWORD fehlt - im Cloud-Modus Pflicht, sonst "
                  "waere die API oeffentlich. Auf Render als "
                  "Umgebungsvariable setzen.")
            sys.exit(1)
        print("JAVIER startet im Cloud-Modus auf Port %d." % port)
        uvicorn.run(app, host="0.0.0.0", port=port)
    elif https:
        print_banner(True)
        uvicorn.run(app, host="0.0.0.0", port=port,
                    ssl_certfile=CERT_FILE, ssl_keyfile=KEY_FILE)
    else:
        print_banner(False)
        uvicorn.run(app, host="0.0.0.0", port=port)
