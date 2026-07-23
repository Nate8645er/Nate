"""Werkzeugregister mit Risikoklassen (Auftrag §6).

Jedes Werkzeug hat eine Risikoklasse. Alles ab „wirkt nach außen" (E-Mail
senden, Zahlung, Löschung, Veröffentlichung) erfordert eine Freigabe, bevor es
ausgeführt wird. Das ist die Grundlage der Genehmigungs-Workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Callable


class RiskClass(IntEnum):
    """Geordnet: höher = riskanter. Ab EXTERNAL ist Freigabe Pflicht."""

    READ = 0            # nur lesen (Suche, Retrieval)
    WRITE_INTERNAL = 1  # interner Zustand (Notiz, Entwurf speichern)
    EXTERNAL = 2        # wirkt nach außen (Mail senden, Zahlung, Veröffentlichung)
    DESTRUCTIVE = 3     # irreversibel (Löschen)


#: Ab dieser Klasse ist eine Freigabe nötig.
APPROVAL_THRESHOLD = RiskClass.EXTERNAL


@dataclass(frozen=True)
class Tool:
    name: str
    risk: RiskClass
    fn: Callable[[dict], object]
    description: str = ""

    def requires_approval(self, threshold: RiskClass = APPROVAL_THRESHOLD) -> bool:
        return self.risk >= threshold

    def execute(self, args: dict) -> object:
        return self.fn(args)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Werkzeug bereits registriert: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def requires_approval(self, name: str, threshold: RiskClass = APPROVAL_THRESHOLD) -> bool:
        tool = self._tools.get(name)
        return bool(tool and tool.requires_approval(threshold))
