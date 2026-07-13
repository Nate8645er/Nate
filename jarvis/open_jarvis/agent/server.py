"""Lokale Bruecke zwischen dem JARVIS Command Center (HUD) und dem Agenten.

Ein winziger HTTP-Server (nur Standardbibliothek), der ausschliesslich an
``127.0.0.1`` lauscht. Er nimmt Sprach-/Text-Befehle vom HUD entgegen und
fuehrt sie mit ``JarvisAgent`` aus.

Endpunkte:
- ``GET  /``        -> liefert das Command-Center-HUD (falls gefunden)
- ``GET  /health``  -> {"ok": true, "models": [...]}
- ``POST /agent``   -> {"task": str, "model": str?, "execute": bool?} -> Agentenlauf als JSON

Sicherheit: bindet nur an localhost, begrenzt die Body-Groesse, fuehrt nur die
sicheren Agent-Werkzeuge aus (keine beliebige Shell). Starten:

    python3 -m open_jarvis.agent --serve            # Port 8765
    python3 -m open_jarvis.agent --serve --port 9000
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from open_jarvis.agent.agent import DEFAULT_WORKSPACE, JarvisAgent, render_run
from open_jarvis.agent.models import list_models, resolve_model

MAX_BODY = 64 * 1024
HUD_PATH = Path(__file__).resolve().parents[2] / "dashboard" / "jarvis_command_center.html"


def run_task(payload: dict[str, Any], *, workspace: Path | str = DEFAULT_WORKSPACE) -> dict[str, Any]:
    """Einen Agentenlauf aus einem Request-Payload erzeugen (testbar ohne Server)."""

    task = str(payload.get("task", "")).strip()
    if not task:
        return {"ok": False, "error": "kein Befehl (task) angegeben"}
    try:
        model = resolve_model(payload.get("model"))
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    execute = bool(payload.get("execute", False))
    agent = JarvisAgent(model=model, workspace=workspace, execute=execute)
    run = agent.run(task)
    result = run.to_dict()
    result["ok"] = True
    result["text"] = render_run(run)
    return result


def _health() -> dict[str, Any]:
    return {"ok": True, "service": "jarvis-agent-bridge", "models": [m.key for m in list_models()]}


class _Handler(BaseHTTPRequestHandler):
    server_version = "JarvisAgentBridge/1.0"
    workspace: Path | str = DEFAULT_WORKSPACE

    def _send(self, code: int, body: dict[str, Any] | bytes, content_type: str = "application/json") -> None:
        if isinstance(body, dict):
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        else:
            data = body
        self.send_response(code)
        self.send_header("Content-Type", content_type + ("; charset=utf-8" if "json" in content_type or "html" in content_type else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:  # noqa: N802 (CORS-Preflight)
        self._send(204, b"")

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/")
        if path == "/favicon.ico":
            self._send(204, b"")
            return
        if path == "/health":
            self._send(200, _health())
            return
        if path == "":
            if HUD_PATH.is_file():
                self._send(200, HUD_PATH.read_bytes(), content_type="text/html")
            else:
                self._send(404, {"ok": False, "error": "HUD nicht gefunden"})
            return
        self._send(404, {"ok": False, "error": "unbekannter Pfad"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/agent":
            self._send(404, {"ok": False, "error": "unbekannter Pfad"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            self._send(413, {"ok": False, "error": "ungueltige oder zu grosse Anfrage"})
            return
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._send(400, {"ok": False, "error": "ungueltiges JSON"})
            return
        if not isinstance(payload, dict):
            self._send(400, {"ok": False, "error": "Payload muss ein Objekt sein"})
            return
        result = run_task(payload, workspace=self.workspace)
        self._send(200 if result.get("ok") else 400, result)

    def log_message(self, *args: Any) -> None:  # Ruhe im Terminal
        return


def serve(host: str = "127.0.0.1", port: int = 8765, *, workspace: Path | str = DEFAULT_WORKSPACE) -> ThreadingHTTPServer:
    """Startet die Bruecke (blockierend). Nur localhost."""

    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("Aus Sicherheitsgruenden nur localhost erlaubt.")
    handler = type("BoundHandler", (_Handler,), {"workspace": workspace})
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"JARVIS-Agent-Bruecke laeuft auf http://{host}:{port}  (HUD: http://{host}:{port}/)")
    print("Beenden mit Strg+C.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nBruecke beendet.")
    finally:
        httpd.server_close()
    return httpd


if __name__ == "__main__":
    serve()
