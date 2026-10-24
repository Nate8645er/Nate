"""Skill system.

A *skill* is a single capability JARVIS can execute — a typed async function
with a name, category, risk level and JSON-schema-ish parameter description.
Skills are what agents (and the LLM, via tool-calling) actually invoke.

Register skills with the @skill decorator; plugins register additional
skills at load time. Every invocation flows through the ApprovalManager
according to its declared risk.
"""

from __future__ import annotations

import inspect
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from jarvis.core.approvals import ApprovalManager, Risk
from jarvis.core.events import EventBus

log = logging.getLogger(__name__)

SkillFunc = Callable[..., Awaitable[Any]]


@dataclass
class Skill:
    name: str
    description: str
    category: str
    risk: Risk
    func: SkillFunc
    parameters: dict[str, Any] = field(default_factory=dict)
    source: str = "builtin"  # "builtin" or plugin id
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "risk": int(self.risk),
            "parameters": self.parameters,
            "source": self.source,
            "enabled": self.enabled,
        }

    def to_tool_schema(self) -> dict[str, Any]:
        """LLM tool-calling schema for this skill."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters,
                "required": [
                    k for k, v in self.parameters.items() if not v.get("optional", False)
                ],
            },
        }


def _infer_parameters(func: SkillFunc) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for name, p in inspect.signature(func).parameters.items():
        if name in ("self", "ctx", "context"):
            continue
        type_map = {int: "integer", float: "number", bool: "boolean", str: "string"}
        json_type = type_map.get(p.annotation, "string")
        entry: dict[str, Any] = {"type": json_type}
        if p.default is not inspect.Parameter.empty:
            entry["optional"] = True
        params[name] = entry
    return params


_PENDING: list[Skill] = []


def skill(
    name: str,
    description: str,
    category: str = "general",
    risk: Risk = Risk.READ,
    parameters: dict[str, Any] | None = None,
) -> Callable[[SkillFunc], SkillFunc]:
    """Declare an async function as a JARVIS skill.

    Module-level skills are collected and attached to the registry when the
    kernel boots (see SkillRegistry.collect_pending).
    """

    def decorator(func: SkillFunc) -> SkillFunc:
        _PENDING.append(
            Skill(
                name=name,
                description=description,
                category=category,
                risk=risk,
                func=func,
                parameters=parameters if parameters is not None else _infer_parameters(func),
            )
        )
        return func

    return decorator


class SkillRegistry:
    def __init__(self, bus: EventBus, approvals: ApprovalManager) -> None:
        self.bus = bus
        self.approvals = approvals
        self._skills: dict[str, Skill] = {}

    # --- registration ---

    def register(self, s: Skill) -> None:
        if s.name in self._skills:
            log.warning("Skill %s re-registered (overriding)", s.name)
        self._skills[s.name] = s

    def collect_pending(self) -> int:
        """Adopt all skills declared via @skill since the last collection."""
        count = 0
        while _PENDING:
            self.register(_PENDING.pop(0))
            count += 1
        return count

    def unregister_source(self, source: str) -> int:
        """Remove all skills registered by a plugin (on unload/disable)."""
        doomed = [n for n, s in self._skills.items() if s.source == source]
        for n in doomed:
            del self._skills[n]
        return len(doomed)

    # --- lookup ---

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def all(self) -> list[Skill]:
        return sorted(self._skills.values(), key=lambda s: (s.category, s.name))

    def enabled(self) -> list[Skill]:
        return [s for s in self.all() if s.enabled]

    def by_category(self, category: str) -> list[Skill]:
        return [s for s in self.enabled() if s.category == category]

    def set_enabled(self, name: str, enabled: bool) -> bool:
        s = self._skills.get(name)
        if s is None:
            return False
        s.enabled = enabled
        return True

    # --- execution ---

    async def invoke(self, name: str, caller: str = "system", **kwargs: Any) -> Any:
        """Execute a skill, gated by user approval according to its risk."""
        s = self._skills.get(name)
        if s is None:
            raise KeyError(f"Unknown skill: {name}")
        if not s.enabled:
            raise PermissionError(f"Skill disabled: {name}")

        detail = ", ".join(f"{k}={v!r}" for k, v in kwargs.items()) or "(no arguments)"
        allowed = await self.approvals.request(
            action=f"skill:{name}", detail=detail, risk=s.risk, requested_by=caller
        )
        if not allowed:
            await self.bus.publish(
                "skill.denied", {"skill": name, "caller": caller}, source="skills"
            )
            raise PermissionError(f"User denied skill: {name}")

        started = time.time()
        try:
            result = await s.func(**kwargs)
            await self.bus.publish(
                "skill.invoked",
                {"skill": name, "caller": caller, "ms": round((time.time() - started) * 1000)},
                source="skills",
            )
            return result
        except Exception as exc:
            await self.bus.publish(
                "skill.failed", {"skill": name, "caller": caller, "error": str(exc)},
                source="skills",
            )
            raise
