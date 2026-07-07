"""Agent framework.

An agent is a long-running async worker with a role, a system prompt, a set
of allowed skill categories, and an inbox of tasks. Agents are *data-driven*:
an AgentSpec fully describes one, so the virtual company can instantiate any
number of specialists (CEO, Coding, Research, …) from YAML without new code.
Custom Python behaviour is possible by subclassing Agent and overriding
handle().

The default handle() runs an LLM tool-loop: the agent thinks with the
configured model and may call any skill it is allowed to use — every
invocation still passes the user-approval gate.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from jarvis.llm.provider import ChatMessage

if TYPE_CHECKING:
    from jarvis.kernel import Kernel

log = logging.getLogger(__name__)


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Task:
    goal: str
    session: str = "default"
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = ""
    created_at: float = field(default_factory=time.time)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "session": self.session,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
        }


@dataclass
class AgentSpec:
    """Declarative description of an agent — enough to instantiate one."""

    name: str  # unique id, e.g. "coding"
    title: str  # display name, e.g. "Coding Agent"
    department: str = "general"
    description: str = ""
    system_prompt: str = ""
    skill_categories: list[str] = field(default_factory=list)  # [] = all categories
    max_tool_rounds: int = 6

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "department": self.department,
            "description": self.description,
            "skill_categories": self.skill_categories,
        }


class Agent:
    """A worker with an inbox. Run any number of these concurrently."""

    def __init__(self, spec: AgentSpec, kernel: "Kernel") -> None:
        self.spec = spec
        self.kernel = kernel
        self.inbox: asyncio.Queue[Task] = asyncio.Queue()
        self.tasks: dict[str, Task] = {}
        self.busy = False
        self._runner: asyncio.Task | None = None

    # --- lifecycle ---

    def start(self) -> None:
        if self._runner is None or self._runner.done():
            self._runner = asyncio.create_task(self._run_loop(), name=f"agent:{self.spec.name}")

    async def stop(self) -> None:
        if self._runner:
            self._runner.cancel()
            try:
                await self._runner
            except asyncio.CancelledError:
                pass
            self._runner = None

    @property
    def running(self) -> bool:
        return self._runner is not None and not self._runner.done()

    # --- task API ---

    async def submit(self, goal: str, session: str = "default", **context: Any) -> Task:
        task = Task(goal=goal, session=session, context=context)
        self.tasks[task.id] = task
        await self.inbox.put(task)
        await self.kernel.bus.publish(
            "agent.task.submitted",
            {"agent": self.spec.name, "task": task.to_dict()},
            source=self.spec.name,
        )
        return task

    async def _run_loop(self) -> None:
        while True:
            task = await self.inbox.get()
            task.status = TaskStatus.RUNNING
            self.busy = True
            await self.kernel.bus.publish(
                "agent.task.started",
                {"agent": self.spec.name, "task": task.to_dict()},
                source=self.spec.name,
            )
            try:
                task.result = await self.handle(task)
                task.status = TaskStatus.DONE
            except asyncio.CancelledError:
                task.status = TaskStatus.FAILED
                task.error = "cancelled"
                raise
            except Exception as exc:  # noqa: BLE001 - agent errors must not kill the loop
                log.exception("Agent %s failed on task %s", self.spec.name, task.id)
                task.status = TaskStatus.FAILED
                task.error = str(exc)
            finally:
                self.busy = False
            await self.kernel.bus.publish(
                "agent.task.completed",
                {"agent": self.spec.name, "task": task.to_dict()},
                source=self.spec.name,
            )

    # --- behaviour (override for custom agents) ---

    def _allowed_tools(self) -> list[dict[str, Any]]:
        skills = self.kernel.skills.enabled()
        if self.spec.skill_categories:
            skills = [s for s in skills if s.category in self.spec.skill_categories]
        return [s.to_tool_schema() for s in skills]

    def _system_prompt(self) -> str:
        base = self.spec.system_prompt or (
            f"Du bist {self.spec.title}, ein spezialisierter Agent im JARVIS AI OS "
            f"(Abteilung: {self.spec.department}). {self.spec.description}"
        )
        return (
            f"{base}\n"
            "Arbeite präzise und knapp. Nutze Werkzeuge (Skills), wenn sie helfen. "
            "Systemeingriffe erfordern Benutzerfreigabe — erledigt der Skill-Layer. "
            "Antworte in der Sprache des Benutzers."
        )

    async def handle(self, task: Task) -> Any:
        """Default: LLM tool-loop with memory context."""
        pack = await self.kernel.memory.context_pack(task.session, task.goal)
        context_note = ""
        if pack["facts"] or pack["preferences"]:
            known = [f"- {f['subject']}: {f['content']}" for f in pack["facts"][:5]]
            known += [f"- (Präferenz) {f['subject']}: {f['content']}" for f in pack["preferences"][:5]]
            context_note = "Bekanntes Wissen:\n" + "\n".join(known)

        messages = [
            ChatMessage(role=m["role"], content=m["content"])
            for m in pack["recent"]
            if m["role"] in ("user", "assistant") and m["content"]
        ]
        if not messages or messages[-1].content != task.goal:
            messages.append(ChatMessage(role="user", content=task.goal))

        system = self._system_prompt()
        if context_note:
            system += "\n\n" + context_note

        tools = self._allowed_tools()
        for _ in range(self.spec.max_tool_rounds):
            result = await self.kernel.llm.chat(messages, system=system, tools=tools)
            if not result.tool_calls:
                return result.text
            # Execute requested skills, then let the model continue.
            for call in result.tool_calls:
                try:
                    output = await self.kernel.skills.invoke(
                        call["name"], caller=self.spec.name, **call.get("arguments", {})
                    )
                    output_text = json.dumps(output, ensure_ascii=False, default=str)[:4000]
                except Exception as exc:  # denied, unknown, or failed skill
                    output_text = f"FEHLER: {exc}"
                messages.append(
                    ChatMessage(role="assistant", content=f"[Tool {call['name']}] angefragt")
                )
                messages.append(
                    ChatMessage(role="user", content=f"[Tool-Ergebnis {call['name']}] {output_text}")
                )
        return result.text or "Werkzeug-Limit erreicht — Teilergebnis siehe Verlauf."
