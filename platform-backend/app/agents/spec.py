"""Deklarative Agent-Definition (Auftrag §6).

Ein Agent ist Konfiguration über gemeinsame Bausteine — keine eigene Codebasis
je Fachagent. Aus einem AgentSpec (YAML/JSON/dict) wird eine Instanz mit
Identität, erlaubten Werkzeugen und harten Grenzen.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Limits:
    """Harte Obergrenzen — schützen vor Endlosläufen und Kostenexplosion."""

    max_steps: int = 12
    max_depth: int = 3
    daily_token_budget: int = 200_000
    max_tokens_per_run: int = 50_000


@dataclass(frozen=True)
class AgentSpec:
    name: str
    role: str                          # z. B. "Kundensupport", "Recherche"
    allowed_tools: frozenset[str] = field(default_factory=frozenset)
    limits: Limits = field(default_factory=Limits)
    system_prompt: str = ""

    @staticmethod
    def from_dict(d: dict) -> "AgentSpec":
        lim = d.get("limits", {})
        return AgentSpec(
            name=d["name"],
            role=d.get("role", ""),
            allowed_tools=frozenset(d.get("allowed_tools", [])),
            limits=Limits(**lim) if lim else Limits(),
            system_prompt=d.get("system_prompt", ""),
        )
