"""Jarvis Ultra: full plugin/skill/tool loadout and the mega-org live ticker."""

from __future__ import annotations

from jarvis_ultra.catalog import all_plugins, all_skills, all_tools, full_loadout, loadout_summary
from jarvis_ultra.mega_org import (
    DEVELOPERS_PER_COMPANY,
    EMPLOYEES_PER_COMPANY,
    company,
    employee,
    format_big,
    org_totals,
    sample_employees,
)

__version__ = "1.0.0"

__all__ = [
    "DEVELOPERS_PER_COMPANY",
    "EMPLOYEES_PER_COMPANY",
    "all_plugins",
    "all_skills",
    "all_tools",
    "company",
    "employee",
    "format_big",
    "full_loadout",
    "loadout_summary",
    "org_totals",
    "sample_employees",
]
