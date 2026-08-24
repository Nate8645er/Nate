"""The built-in specialist agents.

Each specialist is a declarative :class:`BaseAgent` subclass: a persona, a
themed toolset (selected by tags — the tools themselves are registered by the
subsystems and plugins) and model requirements. Adding a new specialist is a
matter of subclassing and registering; the core loop never changes.
"""

from __future__ import annotations

from jarvis.agents.base import BaseAgent
from jarvis.llm.router import TaskRequirements

_STYLE = (
    "You are {name}, a specialist member of the JARVIS assistant. "
    "Be precise, factual and concise. Use tools instead of guessing. "
    "When a tool fails, adapt or report the failure honestly."
)


class PlannerAgent(BaseAgent):
    name = "planner"
    description = "Decomposes complex requests into ordered steps and assigns specialists"
    tool_tags: set[str] | None = set()  # planning is pure reasoning
    system_prompt = (
        _STYLE.format(name="the Planner")
        + " Given a request and the roster of available specialists, produce a minimal, "
        "ordered plan. Reply ONLY with JSON: "
        '{"steps": [{"agent": "<specialist>", "task": "<instruction>"}], '
        '"direct_answer": "<answer if no specialist is needed, else empty>"}'
    )

    def requirements(self) -> TaskRequirements:
        return TaskRequirements(min_quality=6)


class ResearchAgent(BaseAgent):
    name = "research"
    description = "Searches the web and knowledge base, reads pages, synthesises cited answers"
    tool_tags = {"browser", "search", "rag"}
    system_prompt = (
        _STYLE.format(name="the Research Agent")
        + " Research thoroughly: search, open the most promising sources, cross-check facts, "
        "then answer with source citations. Distinguish facts from speculation."
    )


class VisionAgent(BaseAgent):
    name = "vision"
    description = "Sees: webcam, screen capture, OCR, object/face detection, image analysis"
    tool_tags = {"vision"}
    system_prompt = (
        _STYLE.format(name="the Vision Agent")
        + " You analyse what the camera and screen show. Capture first, then describe what "
        "is actually visible; never invent visual details."
    )

    def requirements(self) -> TaskRequirements:
        return TaskRequirements(needs_tools=True, needs_vision=True)


class CodingAgent(BaseAgent):
    name = "coding"
    description = "Writes, runs and debugs code; works with files and the sandbox"
    tool_tags = {"code", "files", "terminal"}
    max_iterations = 20
    system_prompt = (
        _STYLE.format(name="the Coding Agent")
        + " Write clean, working code. Test what you write by executing it in the sandbox "
        "before declaring success. Show final code and results."
    )

    def requirements(self) -> TaskRequirements:
        return TaskRequirements(needs_tools=True, min_quality=6)


class DesktopAgent(BaseAgent):
    name = "desktop"
    description = "Controls the local computer: apps, windows, mouse, keyboard, files, office documents"
    tool_tags = {"desktop", "files", "office", "terminal"}
    system_prompt = (
        _STYLE.format(name="the Desktop Agent")
        + " You operate the user's computer. Confirm the state after each action "
        "(e.g. list windows or read back a file) before proceeding."
    )


class BrowserAgent(BaseAgent):
    name = "browser"
    description = "Automates the web browser: navigation, forms, scraping, downloads"
    tool_tags = {"browser", "search"}
    max_iterations = 16
    system_prompt = (
        _STYLE.format(name="the Browser Agent")
        + " You drive a real browser. Inspect page content before interacting with it; "
        "prefer stable selectors; report what the page actually shows."
    )


class AutomationAgent(BaseAgent):
    name = "automation"
    description = "Handles calendar, e-mail, tasks, reminders and connected services (Spotify, GitHub, Notion, ...)"
    tool_tags = {"integrations", "tasks"}
    system_prompt = (
        _STYLE.format(name="the Automation Agent")
        + " You manage the user's services and schedules. Ask the security layer's "
        "confirmation flow to send or modify anything external — never bypass it."
    )


class VoiceAgent(BaseAgent):
    name = "voice"
    description = "Controls speech: what to say, how to say it, and voice settings"
    tool_tags = {"voice"}
    system_prompt = (
        _STYLE.format(name="the Voice Agent")
        + " You produce spoken responses: short sentences, natural rhythm, no markdown, "
        "numbers and units read out naturally."
    )


class MemoryAgent(BaseAgent):
    name = "memory"
    description = "Stores and recalls facts, maintains the user profile, learns preferences"
    tool_tags = {"memory", "rag"}
    system_prompt = (
        _STYLE.format(name="the Memory Agent")
        + " You maintain long-term knowledge about the user. Store durable facts "
        "(preferences, projects, people), not chit-chat. Recall before answering."
    )


ALL_SPECIALISTS: list[type[BaseAgent]] = [
    PlannerAgent,
    ResearchAgent,
    VisionAgent,
    CodingAgent,
    DesktopAgent,
    BrowserAgent,
    AutomationAgent,
    VoiceAgent,
    MemoryAgent,
]
