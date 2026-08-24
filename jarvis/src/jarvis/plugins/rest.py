"""REST plugins: declarative YAML descriptors that become agent tools.

A REST plugin file describes HTTP endpoints; each endpoint becomes a tool.
Example (``plugins/rest/weather.yaml``)::

    name: openmeteo
    base_url: "https://api.open-meteo.com"
    tools:
      - name: current_weather
        description: "Get current weather for coordinates"
        method: GET
        path: "/v1/forecast"
        query:
          latitude: "{latitude}"
          longitude: "{longitude}"
          current_weather: "true"
        parameters:
          type: object
          properties:
            latitude:  {type: number, description: "Latitude"}
            longitude: {type: number, description: "Longitude"}
          required: [latitude, longitude]

Placeholders ``{param}`` in path, query and body are substituted with tool
arguments; remaining arguments are ignored.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import httpx
import yaml

from jarvis.agents.tools import ToolRegistry
from jarvis.core.errors import PluginError
from jarvis.core.logging import get_logger

logger = get_logger("plugins.rest")

_PLACEHOLDER = re.compile(r"\{(\w+)\}")


def _substitute(template: Any, arguments: dict[str, Any]) -> Any:
    """Recursively substitute {param} placeholders in strings."""
    if isinstance(template, str):
        full = _PLACEHOLDER.fullmatch(template)
        if full and full.group(1) in arguments:
            return arguments[full.group(1)]  # keep native type for full replacements
        return _PLACEHOLDER.sub(
            lambda m: str(arguments.get(m.group(1), m.group(0))), template
        )
    if isinstance(template, dict):
        return {k: _substitute(v, arguments) for k, v in template.items()}
    if isinstance(template, list):
        return [_substitute(v, arguments) for v in template]
    return template


class RestPluginLoader:
    """Loads REST descriptors and registers their endpoints as tools."""

    def __init__(self, tools: ToolRegistry) -> None:
        self._tools = tools
        self._client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def load_file(self, path: Path) -> int:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise PluginError(f"REST plugin {path} is not a mapping")
        return self.load_spec(data, source=f"rest:{data.get('name', path.stem)}")

    def load_spec(self, spec: dict[str, Any], *, source: str) -> int:
        name = spec.get("name") or "rest"
        base_url = str(spec.get("base_url", "")).rstrip("/")
        default_headers = dict(spec.get("headers") or {})
        count = 0
        for tool_spec in spec.get("tools", []):
            tool_name = tool_spec.get("name")
            if not tool_name:
                continue
            qualified = f"{name}_{tool_name}"
            self._tools.register_function(
                qualified,
                tool_spec.get("description", f"REST call {tool_name}"),
                self._make_handler(base_url, default_headers, tool_spec),
                parameters=tool_spec.get("parameters") or {"type": "object", "properties": {}},
                tags={"rest", "plugin", name},
                capability=tool_spec.get("capability"),
                source=source,
            )
            count += 1
        logger.info("REST plugin '%s' registered %d tools", name, count)
        return count

    def _make_handler(
        self, base_url: str, default_headers: dict[str, str], tool_spec: dict[str, Any]
    ):
        method = str(tool_spec.get("method", "GET")).upper()
        path_template = str(tool_spec.get("path", "/"))
        query_template = tool_spec.get("query") or {}
        body_template = tool_spec.get("body")
        headers_template = {**default_headers, **(tool_spec.get("headers") or {})}

        async def handler(**arguments: Any) -> str:
            url = base_url + str(_substitute(path_template, arguments))
            params = {
                k: v for k, v in _substitute(query_template, arguments).items() if v is not None
            }
            headers = _substitute(headers_template, arguments)
            body = _substitute(body_template, arguments) if body_template is not None else None
            response = await self._client.request(
                method, url, params=params or None, json=body, headers=headers or None
            )
            text = response.text[:8000]
            if response.status_code >= 400:
                return f"Error: HTTP {response.status_code}: {text}"
            try:
                return json.dumps(response.json(), ensure_ascii=False)[:8000]
            except (json.JSONDecodeError, ValueError):
                return text

        return handler

    async def aclose(self) -> None:
        await self._client.aclose()
