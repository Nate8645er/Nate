"""JARVIS Enterprise OS — Workforce-Engine, Katalog und Live-Ticker.

Oeffentliche API des Enterprise-Pakets:

- Kennzahlen-Konstanten (``EMPLOYEES_DIRECT``, ``TOTAL_WORKFORCE``, ...)
- :func:`employee` / :func:`workforce_summary` — deterministische Engine
- :class:`LiveTicker` — deterministischer Event-Ticker
- Katalog-Funktionen (``all_skills``, ``catalog_summary``, ...)
"""

from __future__ import annotations

from open_jarvis.enterprise.catalog import (
    AGENT_TOOLS,
    AI_MODELS,
    PLUGIN_CATALOG,
    SHOPIFY_CAPABILITIES,
    SKILL_CATALOG,
    TOOL_CATALOG,
    all_agent_tools,
    all_models,
    all_plugins,
    all_shopify_capabilities,
    all_skills,
    all_tools,
    capability_summary,
    catalog_summary,
    export_catalog,
    export_catalog_json,
)
from open_jarvis.enterprise.live_ticker import DEFAULT_SEED, EVENT_TYPES, LiveTicker
from open_jarvis.enterprise.workforce import (
    COMPANY_DEVELOPERS,
    COMPANY_EMPLOYEES,
    EMPLOYEES_DIRECT,
    TOTAL_DEVELOPERS,
    TOTAL_WORKFORCE,
    employee,
    employee_identity,
    mix64,
    workforce_summary,
)

__all__ = [
    # Kennzahlen
    "EMPLOYEES_DIRECT",
    "COMPANY_EMPLOYEES",
    "COMPANY_DEVELOPERS",
    "TOTAL_WORKFORCE",
    "TOTAL_DEVELOPERS",
    # Engine
    "mix64",
    "employee",
    "employee_identity",
    "workforce_summary",
    # Live-Ticker
    "LiveTicker",
    "DEFAULT_SEED",
    "EVENT_TYPES",
    # Katalog
    "SKILL_CATALOG",
    "PLUGIN_CATALOG",
    "TOOL_CATALOG",
    "all_skills",
    "all_plugins",
    "all_tools",
    "catalog_summary",
    "export_catalog",
    "export_catalog_json",
    # Neu installierte Faehigkeiten (Fable 5 & Co.)
    "AI_MODELS",
    "AGENT_TOOLS",
    "SHOPIFY_CAPABILITIES",
    "all_models",
    "all_agent_tools",
    "all_shopify_capabilities",
    "capability_summary",
]
