"""Agenten-System: Spezialisten mit eigener Rolle und eigenem System-Prompt.

Agenten werden aus Markdown-Dateien geladen (Frontmatter: name, description;
Body: System-Prompt der Rolle). Jarvis lädt damit direkt die Agenten des
ULTRA AI ENTERPRISE OS aus ultra-enterprise-os/agents/.
"""

import logging
from pathlib import Path

from jarvis.core.ollama_client import OllamaClient
from jarvis.utils.markdown_loader import load_directory

logger = logging.getLogger("jarvis.agents")


class AgentRegistry:
    """Lädt Agenten-Definitionen und führt Anfragen an einzelne Agenten aus."""

    def __init__(self, agent_dirs: list[Path]):
        self.agent_dirs = agent_dirs
        #: name -> (meta, system_prompt)
        self.agents: dict[str, tuple[dict, str]] = {}

    def load(self) -> None:
        self.agents = {}
        for directory in self.agent_dirs:
            self.agents.update(load_directory(directory))
        logger.info(
            "%d Agent(en) geladen: %s",
            len(self.agents),
            ", ".join(self.agents) or "keine",
        )

    def get_system_prompt(self, name: str) -> str | None:
        entry = self.agents.get(name)
        return entry[1] if entry else None

    def ask(self, client: OllamaClient, name: str, question: str) -> str:
        """Stellt einem Agenten eine Frage (eigene Rolle, eigener Kontext)."""
        system_prompt = self.get_system_prompt(name)
        if system_prompt is None:
            available = ", ".join(self.agents) or "keine"
            return f"Agent '{name}' gibt es nicht. Verfügbar: {available}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]
        logger.info("Agent '%s' übernimmt die Anfrage.", name)
        return client.chat(messages=messages)

    def overview(self) -> str:
        """Übersicht für /agenten."""
        if not self.agents:
            return "Keine Agenten gefunden."
        lines = []
        for name, (meta, _) in self.agents.items():
            desc = " ".join(str(meta.get("description", "")).split())
            if len(desc) > 100:
                desc = desc[:97] + "..."
            lines.append(f"• {name} - {desc}")
        return "\n".join(lines)
