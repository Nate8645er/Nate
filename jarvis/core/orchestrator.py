"""Orchestrator — the "front desk" of JARVIS.

Takes a user utterance (typed or spoken), decides who should work on it,
and returns the consolidated answer:

  1. Fast paths for built-in commands (remind me, remember, status …).
  2. Explicit delegation: "@coding refactor this" goes straight to an agent.
  3. Keyword routing to a specialist agent when the intent is obvious.
  4. Otherwise the CEO agent handles it (full LLM tool-loop, may itself
     delegate to other agents via the `delegate` skill).

Multiple requests run concurrently — each agent has its own inbox/loop.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from jarvis.agents.base import Task, TaskStatus

if TYPE_CHECKING:
    from jarvis.kernel import Kernel

log = logging.getLogger(__name__)

# Obvious intents → specialist agent. Order matters (first hit wins).
_ROUTES: list[tuple[str, str]] = [
    (r"\b(code|programmier\w*|refactor\w*|bug|funktion|skripte?|script)\b", "coding"),
    (r"\b(recherchier\w*|research|suche im (web|internet)|finde heraus)\b", "research"),
    (r"\b(docker|deploy\w*|server starte\w*|ci/?cd)\b", "devops"),
    (r"\b(browser|webseite öffnen|öffne .*\.(com|de|org))\b", "browser"),
    (r"\b(workflows?|automatisier\w*)\b", "automation"),
    (r"\b(marketing|kampagnen?|werbetexte?|ads?)\b", "marketing"),
    (r"\b(finanz\w*|budgets?|ausgaben|umsatz|kennzahl\w*)\b", "finance"),
    (r"\b(design\w*|layouts?|ui|ux)\b", "design"),
]


class Orchestrator:
    def __init__(self, kernel: "Kernel") -> None:
        self.kernel = kernel

    async def handle_utterance(self, text: str, session: str = "default") -> Task:
        """Route one user message; returns the (running) task."""
        text = text.strip()
        await self.kernel.memory.observe(session, "user", text)
        await self.kernel.bus.publish(
            "chat.user", {"text": text, "session": session}, source="user"
        )

        agent_name = self._pick_agent(text)
        agent = self.kernel.agents.get(agent_name) or self.kernel.agents.get("ceo")
        if agent is None:
            raise RuntimeError("No agents available — is the company staffed?")

        goal = re.sub(r"^@\w+\s*", "", text) if text.startswith("@") else text
        task = await agent.submit(goal, session=session)
        asyncio.create_task(self._announce_result(agent.spec.name, task, session))
        return task

    def _pick_agent(self, text: str) -> str:
        m = re.match(r"^@(\w+)", text)
        if m and self.kernel.agents.get(m.group(1)):
            return m.group(1)
        lowered = text.lower()
        for pattern, agent in _ROUTES:
            if re.search(pattern, lowered) and self.kernel.agents.get(agent):
                return agent
        return "ceo"

    async def _announce_result(self, agent_name: str, task: Task, session: str) -> None:
        """Wait for the task, store + broadcast the answer, speak it."""
        while task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            await asyncio.sleep(0.05)
        if task.status is TaskStatus.DONE:
            answer = str(task.result) if task.result is not None else ""
        else:
            answer = f"Das hat leider nicht geklappt: {task.error}"
        await self.kernel.memory.observe(session, "assistant", answer, agent=agent_name)
        await self.kernel.bus.publish(
            "chat.assistant",
            {"text": answer, "session": session, "agent": agent_name, "task_id": task.id},
            source=agent_name,
        )
        if self.kernel.voice is not None:
            await self.kernel.voice.speak(answer)
