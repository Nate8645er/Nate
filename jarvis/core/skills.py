"""Skill-System: wiederverwendbare Fähigkeiten als Markdown-Prompts.

Ein Skill ist eine .md-Datei im skills/-Ordner mit Frontmatter (name,
description) und einem Prompt als Body. Der Platzhalter {input} wird durch
die Nutzereingabe ersetzt. Neue Skills = neue Datei ablegen, fertig.
"""

import logging
from pathlib import Path

from jarvis.core.ollama_client import OllamaClient
from jarvis.utils.markdown_loader import load_directory

logger = logging.getLogger("jarvis.skills")


class SkillRegistry:
    """Lädt Skills aus einem Ordner und führt sie über das Modell aus."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        #: name -> (meta, prompt_template)
        self.skills: dict[str, tuple[dict, str]] = {}

    def load(self) -> None:
        self.skills = load_directory(self.skills_dir)
        logger.info(
            "%d Skill(s) geladen: %s",
            len(self.skills),
            ", ".join(self.skills) or "keine",
        )

    def run(self, client: OllamaClient, name: str, user_input: str) -> str:
        """Führt einen Skill mit der Nutzereingabe aus."""
        if name not in self.skills:
            available = ", ".join(self.skills) or "keine"
            return f"Skill '{name}' gibt es nicht. Verfügbar: {available}"
        _, template = self.skills[name]
        if "{input}" in template:
            prompt = template.replace("{input}", user_input)
        else:
            prompt = f"{template}\n\n{user_input}"
        return client.chat(prompt=prompt)

    def overview(self) -> str:
        """Übersicht für /skills."""
        if not self.skills:
            return f"Keine Skills gefunden (Ordner: {self.skills_dir})."
        lines = []
        for name, (meta, _) in self.skills.items():
            desc = meta.get("description", "").strip()
            lines.append(f"• /skill {name} <text> - {desc}")
        return "\n".join(lines)
