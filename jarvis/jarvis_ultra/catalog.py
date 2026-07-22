"""Full plugin, skill, and tool catalog shared by Jarvis and every org member."""

from __future__ import annotations

from typing import Any

PLUGINS: tuple[str, ...] = (
    "spotify_control",
    "groq_ai_fallback",
    "gemini_bridge",
    "local_llm",
    "desktop_automation",
    "memory_vault",
    "voice_engine",
    "wake_word",
    "url_safety",
    "provider_health",
    "plugin_marketplace",
    "security_center",
    "health_center",
    "release_toolkit",
    "ultra_enterprise_os",
    "mega_org_live_ticker",
)

SKILLS: tuple[str, ...] = (
    "ultra-enterprise-os",
    "ultra-review",
    "ultra-team",
    "deep-research",
    "dataviz",
    "security-review",
    "code-review",
    "simplify",
    "run",
    "loop",
    "voice-control",
    "automation",
    "memory-privacy",
    "diagnostics",
    "architect",
    "fullstack",
    "qa",
    "security",
    "devops",
    "data-ml",
    "design",
    "docs",
    "business",
    "orchestrator",
    "cod",
    "jarvis-omega",
    "omega-jarvis",
    "omega-enterprise",
    "javier-architect",
    "fable-5",
    "fable-5-turbo",
    "fable-5-max",
    "fable-5-ultra",
    "fable-5-milliarden",
    "milliarden-unternehmen",
    "ultimate-performance",
    "shopify-godmode",
    "shopify-operations",
    "design-taste",
    "impeccable",
    "canvas-design",
    "theme-factory",
    "web-artifacts-builder",
    "skill-creator",
    "morning",
    "docx",
    "pdf",
    "pptx",
    "xlsx",
    "artifact-design",
)

TOOLS: tuple[str, ...] = (
    "Read",
    "Write",
    "Edit",
    "Glob",
    "Grep",
    "Bash",
    "WebSearch",
    "WebFetch",
    "Agent",
    "Workflow",
    "Artifact",
    "Task",
    "Monitor",
    "NotebookEdit",
    "SendMessage",
    "Skill",
    "Cron",
    "Terminal",
)


def all_plugins() -> list[str]:
    """Return every plugin in the catalog."""

    return list(PLUGINS)


def all_skills() -> list[str]:
    """Return every skill in the catalog."""

    return list(SKILLS)


def all_tools() -> list[str]:
    """Return every tool in the catalog."""

    return list(TOOLS)


def full_loadout() -> dict[str, list[str]]:
    """Return the complete loadout granted to Jarvis and every org member."""

    return {"plugins": all_plugins(), "skills": all_skills(), "tools": all_tools()}


def loadout_size() -> int:
    """Return the total number of catalog entries per member."""

    return len(PLUGINS) + len(SKILLS) + len(TOOLS)


def loadout_summary() -> str:
    """Return a short German summary line for ticker and UI output."""

    return f"{len(PLUGINS)} Plugins · {len(SKILLS)} Skills · {len(TOOLS)} Tools — alle aktiv"


def has_full_loadout(entity: dict[str, Any]) -> bool:
    """Return whether an entity dict carries the complete loadout."""

    loadout = entity.get("loadout")
    if not isinstance(loadout, dict):
        return False
    return (
        list(loadout.get("plugins", [])) == list(PLUGINS)
        and list(loadout.get("skills", [])) == list(SKILLS)
        and list(loadout.get("tools", [])) == list(TOOLS)
    )
