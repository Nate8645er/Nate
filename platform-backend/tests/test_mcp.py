"""MCP-Client — getestet gegen einen In-Memory-Fake-Server (kein Prozess/Netz)."""

import pytest

from app.integrations.mcp_client import MCPClient, MCPError


class FakeMCPServer:
    """Minimaler MCP-Server als Transport-Double (JSON-RPC 2.0)."""

    def __init__(self, tools=None, fail_tool=False):
        self._tools = tools or [{"name": "suche", "description": "Websuche"}]
        self._fail_tool = fail_tool

    def roundtrip(self, request: dict) -> dict:
        rid = request.get("id")
        method = request.get("method")
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": rid, "result": {"serverInfo": {"name": "fake", "version": "1"}}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": rid, "result": {"tools": self._tools}}
        if method == "tools/call":
            if self._fail_tool:
                return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32602, "message": "unbekanntes Werkzeug"}}
            name = request["params"]["name"]
            args = request["params"]["arguments"]
            return {"jsonrpc": "2.0", "id": rid,
                    "result": {"content": [{"type": "text", "text": f"{name}({args})"}]}}
        return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "method not found"}}


def test_initialize_und_tools_list():
    c = MCPClient(FakeMCPServer())
    info = c.initialize()
    assert info["serverInfo"]["name"] == "fake"
    tools = c.list_tools()
    assert tools and tools[0]["name"] == "suche"


def test_call_tool_liefert_ergebnis():
    c = MCPClient(FakeMCPServer())
    res = c.call_tool("suche", {"q": "KI"})
    assert res["content"][0]["text"] == "suche({'q': 'KI'})"


def test_auto_initialize_vor_erstem_call():
    # list_tools ohne vorheriges initialize() muss selbst initialisieren
    c = MCPClient(FakeMCPServer())
    assert c.list_tools()[0]["name"] == "suche"


def test_server_fehler_wird_als_mcperror_sichtbar():
    c = MCPClient(FakeMCPServer(fail_tool=True))
    with pytest.raises(MCPError) as ei:
        c.call_tool("gibtsnicht")
    assert ei.value.code == -32602


def test_id_mismatch_wird_erkannt():
    class BadServer:
        def roundtrip(self, request):
            return {"jsonrpc": "2.0", "id": 999, "result": {}}  # falsche id
    with pytest.raises(MCPError):
        MCPClient(BadServer()).initialize()
