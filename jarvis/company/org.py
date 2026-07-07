"""Virtual company: loads an org chart (YAML) and staffs the agent registry.

The org chart is data, not code — hire a new "employee" by adding a YAML
entry or calling Company.hire() at runtime. There is no upper limit on
head-count; each hire is one more Agent in the registry.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from jarvis.agents.base import AgentSpec

if TYPE_CHECKING:
    from jarvis.kernel import Kernel

log = logging.getLogger(__name__)

DEFAULT_ORG = Path(__file__).parent / "org.yaml"


def load_default_org() -> dict[str, Any]:
    with open(DEFAULT_ORG, encoding="utf-8") as f:
        return yaml.safe_load(f)


class Company:
    def __init__(self, kernel: "Kernel") -> None:
        self.kernel = kernel
        self.departments: list[str] = []

    def staff_from_org(self, org: dict[str, Any] | None = None) -> int:
        """Instantiate every agent in the org chart. Returns hire count."""
        org = org or load_default_org()
        self.departments = list(org.get("departments", []))
        hired = 0
        for entry in org.get("agents", []):
            spec = AgentSpec(
                name=entry["name"],
                title=entry.get("title", entry["name"].title()),
                department=entry.get("department", "general"),
                description=entry.get("description", ""),
                system_prompt=entry.get("system_prompt", ""),
                skill_categories=list(entry.get("skill_categories", [])),
            )
            if self.kernel.agents.get(spec.name) is None:
                self.kernel.agents.spawn(spec)
                hired += 1
        log.info("Company staffed: %d agents in %d departments", hired, len(self.departments))
        return hired

    def hire(
        self,
        name: str,
        title: str,
        department: str = "general",
        description: str = "",
        skill_categories: list[str] | None = None,
        system_prompt: str = "",
    ) -> AgentSpec:
        """Hire a new virtual employee at runtime."""
        spec = AgentSpec(
            name=name,
            title=title,
            department=department,
            description=description,
            skill_categories=skill_categories or [],
            system_prompt=system_prompt,
        )
        self.kernel.agents.spawn(spec)
        if department not in self.departments:
            self.departments.append(department)
        return spec

    async def fire(self, name: str) -> bool:
        return await self.kernel.agents.despawn(name)

    def org_chart(self) -> dict[str, Any]:
        chart: dict[str, list[dict]] = {d: [] for d in self.departments}
        for status in self.kernel.agents.status():
            chart.setdefault(status["department"], []).append(status)
        return {"departments": chart}
