"""MCP-Client (Model Context Protocol) über JSON-RPC 2.0.

MCP ist im Zielbild Kern (§B.1). Dieser Client spricht einen MCP-Server
(Plugin) an: initialize → tools/list → tools/call. Der Transport ist ein
Interface (`roundtrip`) → in Tests durch einen Fake-Server ersetzbar, produktiv
durch einen stdio-Subprozess (echter MCP-Server, z. B. `tools/modell-rat-mcp`).

Fehler des Servers werden als `MCPError` sichtbar gemacht, nie stillschweigend
verschluckt.
"""

from __future__ import annotations

import json
import subprocess
from typing import Protocol, runtime_checkable

JSONRPC = "2.0"


class MCPError(Exception):
    def __init__(self, code: int, message: str, data=None) -> None:
        super().__init__(f"MCP-Fehler {code}: {message}")
        self.code = code
        self.data = data


@runtime_checkable
class Transport(Protocol):
    def roundtrip(self, request: dict) -> dict: ...


class JsonRpcClient:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._id = 0

    def call(self, method: str, params: dict | None = None) -> object:
        self._id += 1
        req = {"jsonrpc": JSONRPC, "id": self._id, "method": method}
        if params is not None:
            req["params"] = params
        resp = self._transport.roundtrip(req)
        if resp.get("id") != req["id"]:
            raise MCPError(-32000, f"Antwort-ID passt nicht (erwartet {req['id']}, kam {resp.get('id')})")
        if "error" in resp:
            err = resp["error"]
            raise MCPError(err.get("code", -32000), err.get("message", "unbekannt"), err.get("data"))
        return resp.get("result")


class MCPClient:
    """Minimaler MCP-Client für Werkzeug-Nutzung durch Agenten."""

    def __init__(self, transport: Transport, client_name: str = "platform-backend", version: str = "0.1.0") -> None:
        self._rpc = JsonRpcClient(transport)
        self._client_name = client_name
        self._version = version
        self._initialized = False

    def initialize(self) -> dict:
        result = self._rpc.call("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": self._client_name, "version": self._version},
        })
        self._initialized = True
        return result or {}

    def list_tools(self) -> list[dict]:
        if not self._initialized:
            self.initialize()
        result = self._rpc.call("tools/list")
        return (result or {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict | None = None) -> object:
        if not self._initialized:
            self.initialize()
        return self._rpc.call("tools/call", {"name": name, "arguments": arguments or {}})


class StdioTransport:
    """Echter Transport: newline-getrenntes JSON-RPC gegen einen Subprozess.

    Für produktive MCP-Server (stdio). In Tests wird stattdessen ein Fake-
    Transport benutzt, damit kein Prozess/Netz nötig ist.
    """

    def __init__(self, argv: list[str]) -> None:
        self._proc = subprocess.Popen(  # noqa: S603
            argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1
        )

    def roundtrip(self, request: dict) -> dict:
        assert self._proc.stdin and self._proc.stdout
        self._proc.stdin.write(json.dumps(request) + "\n")
        self._proc.stdin.flush()
        line = self._proc.stdout.readline()
        if not line:
            raise MCPError(-32001, "MCP-Server hat die Verbindung geschlossen")
        return json.loads(line)

    def close(self) -> None:
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
            self._proc.terminate()
        except Exception:  # noqa: BLE001
            pass
