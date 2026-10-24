"""Minimaler MCP-Server (stdio, JSON-RPC 2.0) — ohne externe Abhaengigkeiten.

Stellt den Wissensgraphen als Tools bereit, damit Claude durch den Graphen
navigiert, statt Dateien neu zu lesen:

    claude mcp add graphify -- python3 -m graphify mcp
"""

from __future__ import annotations

import contextlib
import io
import json
import sys

from . import __version__
from .graph import Graph

TOOLS = [
    {
        "name": "graphify_explain",
        "description": (
            "Erklaert einen Knoten des Codebase-Wissensgraphen: Quelldatei+Zeile, "
            "Community, Grad und alle Verbindungen (uses/calls/imports/inherits/"
            "references) — ohne die Datei zu oeffnen. Nutze das VOR dem Lesen von "
            "Dateien, um Architektur und Abhaengigkeiten zu verstehen."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Klassen-/Funktions-/Dateiname"},
                "limit": {"type": "integer", "description": "max. Verbindungen (0 = alle)", "default": 25},
            },
            "required": ["name"],
        },
    },
    {
        "name": "graphify_path",
        "description": (
            "Findet den kuerzesten Beziehungspfad zwischen zwei Symbolen der "
            "Codebase (z. B. wie haengt FastAPI mit ModelField zusammen). "
            "Zero files opened."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "src": {"type": "string", "description": "Startsymbol"},
                "dst": {"type": "string", "description": "Zielsymbol"},
            },
            "required": ["src", "dst"],
        },
    },
    {
        "name": "graphify_search",
        "description": "Sucht Knoten (Klassen, Funktionen, Dateien) im Wissensgraphen per Name.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "graphify_stats",
        "description": "Ueberblick ueber den Wissensgraphen: Knoten, Kanten, Communities, Top-Hubs.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def _run_cli(argv: list[str]) -> str:
    """Fuehrt einen CLI-Befehl aus und faengt stdout/exit ab."""
    from .cli import main

    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            main(argv)
    except SystemExit as exc:
        if exc.code not in (0, None):
            return f"{buf.getvalue()}\n{exc.code}".strip()
    return buf.getvalue().strip() or "(kein Output)"


def _call_tool(name: str, arguments: dict) -> str:
    if name == "graphify_explain":
        limit = int(arguments.get("limit", 25))
        return _run_cli(["explain", str(arguments["name"]), "--limit", str(limit)])
    if name == "graphify_path":
        return _run_cli(["path", str(arguments["src"]), str(arguments["dst"])])
    if name == "graphify_search":
        return _run_cli(["search", str(arguments["query"])])
    if name == "graphify_stats":
        return _run_cli(["stats"])
    raise ValueError(f"Unbekanntes Tool: {name}")


def serve() -> None:
    """JSON-RPC-Schleife auf stdin/stdout (MCP stdio-Transport)."""
    # Graph frueh laden, damit Fehler beim Start sichtbar werden
    if Graph.find_root(".") is None:
        print("Warnung: kein .graphify/graph.json gefunden — zuerst 'graphify scan .' ausfuehren.",
              file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params", {}) or {}

        result = None
        error = None
        if method == "initialize":
            result = {
                "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "graphify", "version": __version__},
            }
        elif method == "notifications/initialized":
            continue  # Notification, keine Antwort
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            try:
                text = _call_tool(params.get("name", ""), params.get("arguments", {}) or {})
                result = {"content": [{"type": "text", "text": text}]}
            except Exception as exc:  # Tool-Fehler als Ergebnis melden
                result = {"content": [{"type": "text", "text": f"Fehler: {exc}"}], "isError": True}
        elif method == "ping":
            result = {}
        elif req_id is None:
            continue  # unbekannte Notification ignorieren
        else:
            error = {"code": -32601, "message": f"Method not found: {method}"}

        if req_id is None:
            continue
        resp: dict = {"jsonrpc": "2.0", "id": req_id}
        if error is not None:
            resp["error"] = error
        else:
            resp["result"] = result
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()
