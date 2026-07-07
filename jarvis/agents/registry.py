"""Agent registry: create, start, stop and look up any number of agents.

Horizontal scaling is a data problem here — every agent is an AgentSpec, so
adding the 20th or the 200th specialist is one registry call (or one YAML
entry in the company org chart). Custom classes can be registered for
specs that need bespoke behaviour.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Type

from jarvis.agents.base import Agent, AgentSpec

if TYPE_CHECKING:
    from jarvis.kernel import Kernel

log = logging.getLogger(__name__)


class AgentRegistry:
    def __init__(self, kernel: "Kernel") -> None:
        self.kernel = kernel
        self._agents: dict[str, Agent] = {}
        self._classes: dict[str, Type[Agent]] = {}

    def register_class(self, spec_name: str, cls: Type[Agent]) -> None:
        """Attach a custom Agent subclass to a spec name."""
        self._classes[spec_name] = cls

    def spawn(self, spec: AgentSpec, start: bool = True) -> Agent:
        if spec.name in self._agents:
            raise ValueError(f"Agent already exists: {spec.name}")
        cls = self._classes.get(spec.name, Agent)
        agent = cls(spec, self.kernel)
        self._agents[spec.name] = agent
        if start:
            agent.start()
        log.info("Agent spawned: %s (%s)", spec.name, spec.title)
        return agent

    async def despawn(self, name: str) -> bool:
        agent = self._agents.pop(name, None)
        if agent is None:
            return False
        await agent.stop()
        return True

    def get(self, name: str) -> Agent | None:
        return self._agents.get(name)

    def all(self) -> list[Agent]:
        return list(self._agents.values())

    def by_department(self, department: str) -> list[Agent]:
        return [a for a in self._agents.values() if a.spec.department == department]

    async def stop_all(self) -> None:
        for agent in self._agents.values():
            await agent.stop()

    def status(self) -> list[dict]:
        return [
            {
                **a.spec.to_dict(),
                "running": a.running,
                "busy": a.busy,
                "queued": a.inbox.qsize(),
                "tasks_total": len(a.tasks),
            }
            for a in self._agents.values()
        ]
