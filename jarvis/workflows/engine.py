"""Workflow engine: declarative multi-step automations.

A workflow is a YAML/JSON document with named steps. Each step either
invokes a skill or delegates a goal to an agent; step outputs are stored
under the step name and can be referenced in later steps with
"{{steps.<name>}}" plus "{{input}}" for the trigger payload.

Example (workflows/morning.yaml):

    name: morning-briefing
    description: Morgendliches Briefing
    steps:
      - name: agenda
        agent: project_manager
        goal: "Fasse meine heutigen Termine und Aufgaben zusammen."
      - name: news
        agent: research
        goal: "Die drei wichtigsten Tech-Nachrichten heute, je ein Satz."
      - name: save
        skill: remember_fact
        args:
          subject: "briefing"
          content: "{{steps.agenda}}"
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from jarvis.agents.base import TaskStatus

if TYPE_CHECKING:
    from jarvis.kernel import Kernel

log = logging.getLogger(__name__)


@dataclass
class Workflow:
    name: str
    description: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            steps=list(data.get("steps", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "steps": self.steps}


def _render(value: Any, scope: dict[str, Any]) -> Any:
    """Substitute {{input}} / {{steps.<name>}} placeholders in strings."""
    if isinstance(value, str):

        def repl(m: re.Match) -> str:
            path = m.group(1).strip()
            node: Any = scope
            for part in path.split("."):
                if isinstance(node, dict) and part in node:
                    node = node[part]
                else:
                    return m.group(0)
            return str(node)

        return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", repl, value)
    if isinstance(value, dict):
        return {k: _render(v, scope) for k, v in value.items()}
    if isinstance(value, list):
        return [_render(v, scope) for v in value]
    return value


class WorkflowEngine:
    def __init__(self, kernel: "Kernel", workflows_dir: Path | None = None) -> None:
        self.kernel = kernel
        self.workflows: dict[str, Workflow] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        if workflows_dir and workflows_dir.is_dir():
            self.load_directory(workflows_dir)

    def load_directory(self, directory: Path) -> int:
        count = 0
        for path in sorted(directory.glob("*.y*ml")):
            try:
                with open(path, encoding="utf-8") as f:
                    self.register(Workflow.from_dict(yaml.safe_load(f)))
                count += 1
            except Exception:  # noqa: BLE001 - a broken file must not kill boot
                log.exception("Failed to load workflow %s", path)
        return count

    def register(self, workflow: Workflow) -> None:
        self.workflows[workflow.name] = workflow

    def remove(self, name: str) -> bool:
        return self.workflows.pop(name, None) is not None

    async def run(self, name: str, input_data: Any = None, session: str = "default") -> dict[str, Any]:
        wf = self.workflows.get(name)
        if wf is None:
            raise KeyError(f"Unknown workflow: {name}")

        run_id = uuid.uuid4().hex[:12]
        scope: dict[str, Any] = {"input": input_data, "steps": {}}
        record: dict[str, Any] = {"id": run_id, "workflow": name, "status": "running", "steps": {}}
        self.runs[run_id] = record
        await self.kernel.bus.publish("workflow.started", {"id": run_id, "workflow": name})

        try:
            for step in wf.steps:
                step_name = step.get("name") or f"step{len(scope['steps']) + 1}"
                if "skill" in step:
                    args = _render(step.get("args", {}), scope)
                    output = await self.kernel.skills.invoke(
                        step["skill"], caller=f"workflow:{name}", **args
                    )
                elif "agent" in step:
                    agent = self.kernel.agents.get(step["agent"])
                    if agent is None:
                        raise KeyError(f"Unknown agent in workflow: {step['agent']}")
                    goal = _render(step.get("goal", ""), scope)
                    task = await agent.submit(goal, session=session)
                    while task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                        import asyncio

                        await asyncio.sleep(0.05)
                    if task.status is TaskStatus.FAILED:
                        raise RuntimeError(f"Agent step failed: {task.error}")
                    output = task.result
                else:
                    raise ValueError(f"Step {step_name} needs 'skill' or 'agent'")
                scope["steps"][step_name] = output
                record["steps"][step_name] = output
            record["status"] = "done"
        except Exception as exc:
            record["status"] = "failed"
            record["error"] = str(exc)
            await self.kernel.bus.publish(
                "workflow.failed", {"id": run_id, "workflow": name, "error": str(exc)}
            )
            raise
        await self.kernel.bus.publish("workflow.completed", {"id": run_id, "workflow": name})
        return record
