"""Model Context Protocol (MCP) client.

Connects to MCP servers over stdio (JSON-RPC 2.0, newline-delimited) or
streamable HTTP, lists their tools and registers each one in the JARVIS tool
registry — so any MCP server becomes a set of agent tools without core
changes.

Configuration (``config.yaml``)::

    plugins:
      mcp_servers:
        filesystem:
          command: "npx"
          args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
        remote:
          url: "https://example.com/mcp"
          headers: {"Authorization": "Bearer ..."}
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from jarvis.agents.tools import ToolRegistry
from jarvis.core.errors import PluginError
from jarvis.core.logging import get_logger

logger = get_logger("plugins.mcp")

_PROTOCOL_VERSION = "2025-03-26"
_CLIENT_INFO = {"name": "jarvis", "version": "1.0.0"}


class McpStdioClient:
    """JSON-RPC 2.0 client speaking MCP over a child process's stdio."""

    def __init__(self, name: str, command: str, args: list[str], env: dict[str, str] | None = None) -> None:
        self.name = name
        self._command = command
        self._args = args
        self._env = env
        self._proc: asyncio.subprocess.Process | None = None
        self._pending: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self._next_id = 0
        self._reader_task: asyncio.Task | None = None
        self._write_lock = asyncio.Lock()

    async def start(self) -> None:
        self._proc = await asyncio.create_subprocess_exec(
            self._command,
            *self._args,
            env=self._env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        self._reader_task = asyncio.get_running_loop().create_task(self._read_loop())
        await self._request(
            "initialize",
            {
                "protocolVersion": _PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": _CLIENT_INFO,
            },
        )
        await self._notify("notifications/initialized", {})

    async def _read_loop(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        try:
            while True:
                line = await self._proc.stdout.readline()
                if not line:
                    break
                try:
                    message = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                msg_id = message.get("id")
                if msg_id is not None and msg_id in self._pending:
                    self._pending.pop(msg_id).set_result(message)
        except asyncio.CancelledError:
            pass
        finally:
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(PluginError(f"MCP server '{self.name}' closed"))
            self._pending.clear()

    async def _send(self, payload: dict[str, Any]) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise PluginError(f"MCP server '{self.name}' is not running")
        data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        async with self._write_lock:
            self._proc.stdin.write(data)
            await self._proc.stdin.drain()

    async def _notify(self, method: str, params: dict[str, Any]) -> None:
        await self._send({"jsonrpc": "2.0", "method": method, "params": params})

    async def _request(self, method: str, params: dict[str, Any], timeout: float = 60.0) -> dict[str, Any]:
        self._next_id += 1
        msg_id = self._next_id
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._pending[msg_id] = future
        await self._send({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params})
        try:
            message = await asyncio.wait_for(future, timeout=timeout)
        except TimeoutError as exc:
            self._pending.pop(msg_id, None)
            raise PluginError(f"MCP '{self.name}' request '{method}' timed out") from exc
        if "error" in message:
            raise PluginError(f"MCP '{self.name}' error: {message['error']}")
        return message.get("result", {})

    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self._request("tools/list", {})
        return result.get("tools", [])

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        result = await self._request("tools/call", {"name": name, "arguments": arguments})
        return _render_content(result)

    async def stop(self) -> None:
        if self._reader_task is not None:
            self._reader_task.cancel()
            self._reader_task = None
        if self._proc is not None:
            if self._proc.returncode is None:
                self._proc.terminate()
                try:
                    await asyncio.wait_for(self._proc.wait(), timeout=5)
                except TimeoutError:
                    self._proc.kill()
                    await self._proc.wait()
            self._proc = None


class McpHttpClient:
    """MCP over streamable HTTP (single-endpoint JSON-RPC POSTs)."""

    def __init__(self, name: str, url: str, headers: dict[str, str] | None = None) -> None:
        self.name = name
        self._url = url
        self._client = httpx.AsyncClient(
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                **(headers or {}),
            },
            timeout=60.0,
        )
        self._next_id = 0
        self._session_id: str | None = None

    async def start(self) -> None:
        result = await self._request(
            "initialize",
            {
                "protocolVersion": _PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": _CLIENT_INFO,
            },
        )
        logger.debug("MCP http '%s' initialized: %s", self.name, result.get("serverInfo", {}))
        await self._post({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    async def _post(self, payload: dict[str, Any]) -> httpx.Response:
        headers = {}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        response = await self._client.post(self._url, json=payload, headers=headers)
        if session := response.headers.get("Mcp-Session-Id"):
            self._session_id = session
        return response

    async def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._next_id += 1
        response = await self._post(
            {"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": params}
        )
        if response.status_code >= 400:
            raise PluginError(
                f"MCP http '{self.name}' returned HTTP {response.status_code}: {response.text[:300]}"
            )
        message = _parse_http_body(response)
        if "error" in message:
            raise PluginError(f"MCP '{self.name}' error: {message['error']}")
        return message.get("result", {})

    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self._request("tools/list", {})
        return result.get("tools", [])

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        result = await self._request("tools/call", {"name": name, "arguments": arguments})
        return _render_content(result)

    async def stop(self) -> None:
        await self._client.aclose()


def _parse_http_body(response: httpx.Response) -> dict[str, Any]:
    """Handle plain-JSON and SSE-framed responses."""
    content_type = response.headers.get("content-type", "")
    if "text/event-stream" in content_type:
        for line in response.text.splitlines():
            if line.startswith("data:"):
                try:
                    parsed = json.loads(line[5:].strip())
                    if isinstance(parsed, dict) and ("result" in parsed or "error" in parsed):
                        return parsed
                except json.JSONDecodeError:
                    continue
        return {}
    try:
        parsed = response.json()
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _render_content(result: dict[str, Any]) -> str:
    """Flatten MCP tool-result content blocks to text."""
    parts: list[str] = []
    for block in result.get("content", []):
        block_type = block.get("type")
        if block_type == "text":
            parts.append(block.get("text", ""))
        elif block_type == "resource":
            resource = block.get("resource", {})
            parts.append(resource.get("text", resource.get("uri", "")))
        else:
            parts.append(json.dumps(block, ensure_ascii=False))
    if result.get("isError"):
        return "Error: " + ("\n".join(parts) or "MCP tool reported an error")
    return "\n".join(parts) or "OK"


class McpManager:
    """Starts configured MCP servers and mirrors their tools into the registry."""

    def __init__(self, tools: ToolRegistry) -> None:
        self._tools = tools
        self._clients: dict[str, McpStdioClient | McpHttpClient] = {}

    async def start_server(self, name: str, spec: dict[str, Any]) -> int:
        """Start one MCP server from its config spec; returns number of tools."""
        client: McpStdioClient | McpHttpClient
        if spec.get("url"):
            client = McpHttpClient(name, spec["url"], spec.get("headers"))
        elif spec.get("command"):
            client = McpStdioClient(name, spec["command"], list(spec.get("args", [])), spec.get("env"))
        else:
            raise PluginError(f"MCP server '{name}' needs either 'command' or 'url'")
        await client.start()
        self._clients[name] = client

        count = 0
        for tool in await client.list_tools():
            tool_name = tool.get("name", "")
            if not tool_name:
                continue
            qualified = f"mcp_{name}_{tool_name}"

            def make_handler(c: McpStdioClient | McpHttpClient, t: str):
                async def handler(**arguments: Any) -> str:
                    return await c.call_tool(t, arguments)

                return handler

            self._tools.register_function(
                qualified,
                tool.get("description", f"MCP tool {tool_name} from {name}"),
                make_handler(client, tool_name),
                parameters=tool.get("inputSchema") or {"type": "object", "properties": {}},
                tags={"mcp", name},
                capability=f"mcp.{name}",
                source=f"mcp:{name}",
            )
            count += 1
        logger.info("MCP server '%s' connected with %d tools", name, count)
        return count

    async def start_all(self, servers: dict[str, dict[str, Any]]) -> None:
        for name, spec in servers.items():
            try:
                await self.start_server(name, spec)
            except Exception as exc:
                logger.error("MCP server '%s' failed to start: %s", name, exc)

    async def stop_all(self) -> None:
        for name, client in list(self._clients.items()):
            self._tools.unregister_source(f"mcp:{name}")
            try:
                await client.stop()
            except Exception:
                logger.exception("Stopping MCP server '%s' failed", name)
        self._clients.clear()
