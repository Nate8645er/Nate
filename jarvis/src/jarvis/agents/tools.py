"""Tool abstraction and registry.

A :class:`Tool` couples a JSON-schema description (shown to the model) with an
async handler and a security capability. Tools are registered centrally with
*tags* so agents can request a themed subset ("desktop", "browser", ...).
Plugins register tools through the same API, which is what makes the system
extensible without core changes.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from jarvis.core.errors import PermissionDeniedError, ToolError
from jarvis.core.logging import get_logger
from jarvis.core.security import PermissionManager
from jarvis.llm.base import ToolSpec

logger = get_logger("agents.tools")

ToolHandler = Callable[..., Awaitable[Any] | Any]


@dataclass(slots=True)
class Tool:
    """A callable capability exposed to LLM agents."""

    name: str
    description: str
    handler: ToolHandler
    parameters: dict[str, Any] = field(
        default_factory=lambda: {"type": "object", "properties": {}}
    )
    tags: set[str] = field(default_factory=set)
    capability: str | None = None  # security capability; None => no confirmation needed
    source: str = "core"  # "core", plugin name, or MCP server name

    def spec(self) -> ToolSpec:
        return ToolSpec(name=self.name, description=self.description, parameters=self.parameters)


def _render_result(result: Any) -> str:
    if result is None:
        return "OK"
    if isinstance(result, str):
        return result
    try:
        return json.dumps(result, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(result)


class ToolRegistry:
    """Central, permission-aware tool registry."""

    def __init__(self, permissions: PermissionManager | None = None) -> None:
        self._tools: dict[str, Tool] = {}
        self._permissions = permissions

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            logger.warning("Tool '%s' re-registered (source %s)", tool.name, tool.source)
        self._tools[tool.name] = tool

    def register_function(
        self,
        name: str,
        description: str,
        handler: ToolHandler,
        *,
        parameters: dict[str, Any] | None = None,
        tags: set[str] | None = None,
        capability: str | None = None,
        source: str = "core",
    ) -> Tool:
        tool = Tool(
            name=name,
            description=description,
            handler=handler,
            parameters=parameters or {"type": "object", "properties": {}},
            tags=tags or set(),
            capability=capability,
            source=source,
        )
        self.register(tool)
        return tool

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def unregister_source(self, source: str) -> int:
        """Remove all tools from a source (used on plugin unload/reload)."""
        names = [n for n, t in self._tools.items() if t.source == source]
        for name in names:
            del self._tools[name]
        return len(names)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def by_tags(self, tags: set[str] | None) -> list[Tool]:
        """Tools matching any of the tags; ``None`` selects everything."""
        if tags is None:
            return self.all()
        return [t for t in self._tools.values() if t.tags & tags]

    def specs(self, tags: set[str] | None = None) -> list[ToolSpec]:
        return [t.spec() for t in self.by_tags(tags)]

    async def execute(self, name: str, arguments: dict[str, Any]) -> str:
        """Run a tool with permission check; returns a string for the model."""
        tool = self._tools.get(name)
        if tool is None:
            return f"Error: unknown tool '{name}'"
        if tool.capability and self._permissions is not None:
            description = f"{name}({json.dumps(arguments, ensure_ascii=False, default=str)[:300]})"
            try:
                await self._permissions.check(tool.capability, description)
            except PermissionDeniedError as exc:
                return f"Permission denied: {exc.message}"
        try:
            if inspect.iscoroutinefunction(tool.handler):
                outcome = await tool.handler(**arguments)
            else:
                # Run sync handlers in a worker thread so they cannot block the loop.
                loop = asyncio.get_running_loop()
                outcome = await loop.run_in_executor(
                    None, functools.partial(tool.handler, **arguments)
                )
                if inspect.isawaitable(outcome):
                    outcome = await outcome
            return _render_result(outcome)
        except TypeError as exc:
            return f"Error: invalid arguments for '{name}': {exc}"
        except ToolError as exc:
            return f"Error: {exc.message}"
        except Exception as exc:
            logger.exception("Tool '%s' failed", name)
            return f"Error: {type(exc).__name__}: {exc}"
