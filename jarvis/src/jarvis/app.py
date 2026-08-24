"""Application assembly: builds and wires every subsystem via the DI container.

:class:`JarvisApp` is the composition root. Optional subsystems (voice,
vision, desktop, browser, integrations) are activated when (a) enabled in
config and (b) their dependencies import cleanly; each exposes a module-level
``register(app: JarvisApp) -> None`` hook that adds its tools and services.
That contract also keeps the core closed against modification while staying
open for extension.
"""

from __future__ import annotations

import importlib
from typing import Any

from jarvis.agents.base import AgentResult, BaseAgent
from jarvis.agents.core_tools import register_core_tools
from jarvis.agents.orchestrator import AgentOrchestrator
from jarvis.agents.specialists import ALL_SPECIALISTS
from jarvis.agents.tools import ToolRegistry
from jarvis.core.config import JarvisConfig, load_config
from jarvis.core.container import ServiceContainer
from jarvis.core.events import EventBus
from jarvis.core.logging import get_logger, setup_logging
from jarvis.core.security import PermissionManager, PythonSandbox
from jarvis.llm.base import Message
from jarvis.llm.registry import ProviderRegistry
from jarvis.llm.router import ModelRouter
from jarvis.memory.long_term import LongTermMemory
from jarvis.memory.manager import MemoryManager
from jarvis.memory.rag import RagPipeline
from jarvis.memory.vector_store import (
    HashingEmbedder,
    ProviderEmbedder,
    create_vector_store,
)
from jarvis.plugins.api import PluginContext
from jarvis.plugins.loader import PluginLoader
from jarvis.plugins.mcp import McpManager
from jarvis.plugins.rest import RestPluginLoader

logger = get_logger("app")

# (module, config attribute with an `.enabled` flag; None = always try)
_SUBSYSTEMS: list[tuple[str, str | None]] = [
    ("jarvis.vision", "vision"),
    ("jarvis.desktop", "desktop"),
    ("jarvis.browser", "browser"),
    ("jarvis.integrations", None),
    ("jarvis.voice", "voice"),
]


class JarvisApp:
    """The assembled assistant. Create with :meth:`create`, dispose with :meth:`aclose`."""

    def __init__(self, config: JarvisConfig) -> None:
        self.config = config
        self.container = ServiceContainer()
        self.events = EventBus()
        self.permissions = PermissionManager(config)
        self.tools = ToolRegistry(self.permissions)
        self.providers = ProviderRegistry(config)
        self.router = ModelRouter(config, self.providers)
        self.orchestrator = AgentOrchestrator(self.router, self.events)
        self.sandbox = PythonSandbox()
        self.memory: MemoryManager | None = None
        self.plugin_loader: PluginLoader | None = None
        self.mcp = McpManager(self.tools)
        self.rest_plugins = RestPluginLoader(self.tools)
        self.active_subsystems: list[str] = []

    # -- lifecycle ----------------------------------------------------------------

    @classmethod
    async def create(cls, config: JarvisConfig | None = None) -> JarvisApp:
        config = config or load_config()
        config.ensure_dirs()
        setup_logging(config.log_level, config.data_dir / "logs")
        app = cls(config)
        await app._start()
        return app

    async def _start(self) -> None:
        # Memory stack.
        long_term = LongTermMemory(self.config.resolve_path(self.config.memory.database_file))
        await long_term.open()
        embedder = (
            ProviderEmbedder(self.router)
            if self.config.memory.embedding_provider
            else HashingEmbedder()
        )
        vector_store = create_vector_store(
            self.config.memory.vector_backend,
            embedder,
            self.config.data_dir,
            self.config.memory.vector_collection,
        )
        rag = RagPipeline(
            vector_store,
            chunk_size=self.config.memory.rag_chunk_size,
            chunk_overlap=self.config.memory.rag_chunk_overlap,
            top_k=self.config.memory.rag_top_k,
        )
        self.memory = MemoryManager(self.config, long_term, vector_store, rag)
        self.container.register_instance(MemoryManager, self.memory)
        self.container.on_close(long_term.close)

        # Core services into the container for subsystems/plugins.
        self.container.register_instance(JarvisConfig, self.config)
        self.container.register_instance(EventBus, self.events)
        self.container.register_instance(ToolRegistry, self.tools)
        self.container.register_instance(PermissionManager, self.permissions)
        self.container.register_instance(ModelRouter, self.router)
        self.container.register_instance(AgentOrchestrator, self.orchestrator)

        register_core_tools(self.tools, self.memory, self.sandbox)

        # Optional subsystems.
        for module_name, config_attr in _SUBSYSTEMS:
            if config_attr is not None and not getattr(self.config, config_attr).enabled:
                continue
            try:
                module = importlib.import_module(module_name)
                module.register(self)
                self.active_subsystems.append(module_name.rsplit(".", 1)[-1])
            except ImportError as exc:
                logger.info("Subsystem %s inactive (missing dependency: %s)", module_name, exc)
            except Exception:
                logger.exception("Subsystem %s failed to initialise", module_name)

        # Specialist agents (after subsystem tools exist).
        for agent_type in ALL_SPECIALISTS:
            self.orchestrator.register(agent_type(self.router, self.tools, self.events))

        # Plugins: local Python plugins, MCP servers, REST descriptors.
        if self.config.plugins.enabled:
            directories = [self.config.resolve_path(d) for d in self.config.plugins.directories]
            self.plugin_loader = PluginLoader(self._plugin_context, directories)
            await self.plugin_loader.load_all()
            await self.mcp.start_all(self.config.plugins.mcp_servers)
            for descriptor in self.config.plugins.rest_plugins:
                path = self.config.resolve_path(descriptor)
                if path.is_file():
                    await self.rest_plugins.load_file(path)

        await self.events.publish("app.started", {"subsystems": self.active_subsystems})
        logger.info(
            "JARVIS online. Subsystems: %s | Tools: %d | Agents: %s",
            ", ".join(self.active_subsystems) or "core only",
            len(self.tools.all()),
            ", ".join(self.orchestrator.roster()),
        )

    def start_hot_reload(self) -> None:
        """Enable plugin hot reload (needs a running event loop)."""
        if self.plugin_loader is not None and self.config.plugins.hot_reload:
            self.plugin_loader.start_watching()

    def _plugin_context(self, name: str) -> PluginContext:
        return PluginContext(
            config=self.config,
            tools=self.tools,
            events=self.events,
            router=self.router,
            orchestrator=self.orchestrator,
            memory=self.memory,
            _plugin_name=name,
        )

    async def aclose(self) -> None:
        await self.events.publish("app.stopping", {})
        if self.plugin_loader is not None:
            await self.plugin_loader.unload_all()
        await self.mcp.stop_all()
        await self.rest_plugins.aclose()
        await self.providers.aclose()
        await self.container.aclose()

    # -- primary entry points ------------------------------------------------------

    def _jarvis_persona(self) -> str:
        cfg = self.config
        return (
            f"You are {cfg.assistant_name}, a highly capable personal AI assistant "
            f"inspired by the JARVIS of Tony Stark. Address the user as {cfg.user_name}. "
            f"Default language: {cfg.language}. You are precise, dryly witty when "
            "appropriate, and honest about uncertainty and failures. You can delegate to "
            "specialist agents and tools for research, vision, desktop, browser, voice, "
            "automation, coding and memory work."
        )

    async def ask(self, text: str, *, use_orchestrator: bool = True) -> AgentResult:
        """Answer a user request with memory context, optionally via multi-agent planning."""
        assert self.memory is not None
        await self.memory.add_turn(Message.user(text))
        memory_context = await self.memory.recall(text)
        context = "\n\n".join(filter(None, [self._jarvis_persona(), memory_context]))

        if use_orchestrator and len(self.orchestrator.roster()) > 1:
            result = await self.orchestrator.run(text, context=context)
        else:
            agent = BaseAgent(
                self.router,
                self.tools,
                self.events,
                name="jarvis",
                description="JARVIS main loop",
                system_prompt=context,
            )
            result = await agent.run(text, history=self.memory.window()[:-1])

        await self.memory.add_turn(Message.assistant(result.output))
        await self.events.publish("chat.answer", {"text": result.output})
        return result

    async def ask_stream(self, text: str) -> Any:
        """Streaming single-agent answer (used by API/GUI/voice for low latency)."""
        assert self.memory is not None
        await self.memory.add_turn(Message.user(text))
        memory_context = await self.memory.recall(text)
        context = "\n\n".join(filter(None, [self._jarvis_persona(), memory_context]))
        agent = BaseAgent(
            self.router,
            self.tools,
            self.events,
            name="jarvis",
            description="JARVIS main loop",
            system_prompt=context,
        )
        async for item in agent.run_stream(text, history=self.memory.window()[:-1]):
            if isinstance(item, AgentResult):
                await self.memory.add_turn(Message.assistant(item.output))
                await self.events.publish("chat.answer", {"text": item.output})
            yield item

    def status(self) -> dict[str, Any]:
        return {
            "assistant": self.config.assistant_name,
            "subsystems": self.active_subsystems,
            "agents": self.orchestrator.roster(),
            "tools": sorted(t.name for t in self.tools.all()),
            "plugins": sorted(self.plugin_loader.loaded) if self.plugin_loader else [],
        }
