"""The JARVIS kernel: owns every subsystem and wires them together.

Boot order matters: bus -> approvals -> memory -> llm -> skills -> agents
-> company -> plugins -> workflows -> scheduler -> voice -> orchestrator.
The FastAPI layer talks only to this object.
"""

from __future__ import annotations

import logging

from jarvis.agents.registry import AgentRegistry
from jarvis.automation.scheduler import Scheduler
from jarvis.company.org import Company
from jarvis.config import Settings
from jarvis.config import settings as default_settings
from jarvis.core.approvals import ApprovalManager
from jarvis.core.events import EventBus
from jarvis.core.orchestrator import Orchestrator
from jarvis.llm.provider import LLMProvider, create_provider
from jarvis.memory.manager import MemoryManager
from jarvis.plugins.manager import PluginManager
from jarvis.skills.base import SkillRegistry
from jarvis.skills.builtin import register_builtin_skills
from jarvis.voice.pipeline import VoicePipeline
from jarvis.workflows.engine import WorkflowEngine

log = logging.getLogger(__name__)


class Kernel:
    def __init__(self, cfg: Settings | None = None) -> None:
        self.settings = cfg or default_settings
        self.settings.ensure_dirs()

        self.bus = EventBus()
        self.approvals = ApprovalManager(
            self.bus,
            threshold=self.settings.approval_threshold,
            timeout=self.settings.approval_timeout_seconds,
        )
        self.memory = MemoryManager(
            self.settings.data_dir, vector_backend=self.settings.vector_backend
        )
        self.llm: LLMProvider = create_provider(self.settings)
        self.skills = SkillRegistry(self.bus, self.approvals)
        self.agents = AgentRegistry(self)
        self.company = Company(self)
        self.plugins = PluginManager(self, self.settings.plugins_dir)
        self.workflows = WorkflowEngine(self, self.settings.workflows_dir)
        self.scheduler = Scheduler(self)
        self.voice: VoicePipeline | None = None
        self.orchestrator = Orchestrator(self)
        self._started = False

    async def start(self) -> None:
        if self._started:
            return
        register_builtin_skills(self)
        self.skills.collect_pending()
        self.company.staff_from_org()
        await self.plugins.load_all()
        self.scheduler.start()
        if self.settings.voice_enabled:
            self.voice = VoicePipeline(self)
        self._started = True
        await self.bus.publish(
            "system.online",
            {
                "assistant": self.settings.assistant_name,
                "agents": len(self.agents.all()),
                "skills": len(self.skills.all()),
                "plugins": len(self.plugins.plugins),
                "llm": self.llm.name,
            },
        )
        log.info(
            "JARVIS online — %d agents, %d skills, LLM=%s",
            len(self.agents.all()), len(self.skills.all()), self.llm.name,
        )

    async def stop(self) -> None:
        if not self._started:
            return
        await self.scheduler.stop()
        await self.agents.stop_all()
        self.memory.close()
        self._started = False
        log.info("JARVIS offline")
