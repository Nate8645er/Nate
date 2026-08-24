"""Public plugin API.

A plugin is a directory containing ``plugin.py`` that defines a subclass of
:class:`Plugin` (or a module-level ``plugin`` instance). On load, JARVIS calls
:meth:`Plugin.setup` with a :class:`PluginContext`, through which the plugin
registers tools, agents, LLM providers, event handlers and FastAPI routes.
Everything registered is tracked by the plugin's name so a reload cleanly
replaces it.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from jarvis.agents.base import BaseAgent
from jarvis.agents.tools import Tool, ToolRegistry
from jarvis.core.config import JarvisConfig
from jarvis.core.events import EventBus, EventHandler, Subscription
from jarvis.core.logging import get_logger
from jarvis.llm.router import ModelRouter

if TYPE_CHECKING:
    from fastapi import APIRouter

    from jarvis.agents.orchestrator import AgentOrchestrator
    from jarvis.memory.manager import MemoryManager

logger = get_logger("plugins.api")


class PluginManifest(BaseModel):
    """Metadata declared by a plugin (``manifest`` attribute or plugin.yaml)."""

    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    requires: list[str] = Field(default_factory=list)  # pip requirements (informational)
    tags: list[str] = Field(default_factory=list)


@dataclass
class PluginContext:
    """Everything a plugin may talk to, handed over at setup time."""

    config: JarvisConfig
    tools: ToolRegistry
    events: EventBus
    router: ModelRouter
    orchestrator: AgentOrchestrator | None = None
    memory: MemoryManager | None = None
    _plugin_name: str = "plugin"
    _subscriptions: list[Subscription] = field(default_factory=list)
    _agent_names: list[str] = field(default_factory=list)
    _api_routers: list[Any] = field(default_factory=list)

    # -- registration helpers (tracked for clean unload) --------------------------

    def register_tool(
        self,
        name: str,
        description: str,
        handler: Callable[..., Awaitable[Any] | Any],
        *,
        parameters: dict[str, Any] | None = None,
        tags: set[str] | None = None,
        capability: str | None = None,
    ) -> Tool:
        return self.tools.register_function(
            name,
            description,
            handler,
            parameters=parameters,
            tags=(tags or set()) | {"plugin", self._plugin_name},
            capability=capability,
            source=self._plugin_name,
        )

    def register_agent(self, agent: BaseAgent) -> None:
        if self.orchestrator is None:
            logger.warning("Plugin %s registered agent before orchestrator exists", self._plugin_name)
            return
        self.orchestrator.register(agent)
        self._agent_names.append(agent.name)

    def subscribe(self, pattern: str, handler: EventHandler) -> Subscription:
        sub = self.events.subscribe(pattern, handler)
        self._subscriptions.append(sub)
        return sub

    def register_api_router(self, api_router: APIRouter) -> None:
        """Expose extra HTTP endpoints; mounted under /plugins/<name> by the server."""
        self._api_routers.append(api_router)

    # -- teardown -------------------------------------------------------------------

    def _teardown(self) -> None:
        for sub in self._subscriptions:
            sub.cancel()
        self._subscriptions.clear()
        if self.orchestrator is not None:
            for agent_name in self._agent_names:
                self.orchestrator.unregister(agent_name)
        self._agent_names.clear()
        self.tools.unregister_source(self._plugin_name)


class Plugin:
    """Base class for JARVIS plugins."""

    manifest: PluginManifest = PluginManifest(name="unnamed")

    async def setup(self, context: PluginContext) -> None:
        """Register tools/agents/handlers. Called once on load."""

    async def teardown(self) -> None:
        """Release plugin-owned resources. Called on unload/reload."""
