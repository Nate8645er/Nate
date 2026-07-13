"""Skills-System für JARVIS — im Stil von Claude Code / Claude.ai Skills.

Ein Skill ist eine Markdown-Datei in jarvis/skills/ mit einem kurzen
Front-Matter-Block (Name + Beschreibung) und einer Anleitung. Skills werden
dynamisch geladen und können einem Gehirn-Task als Kontext vorangestellt
werden ("Skill anwenden"). So lassen sich Fähigkeiten hinzufügen, ohne Code
zu ändern — genau wie bei Claude Code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    name: str
    description: str
    body: str


def _parse(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8")
    name = path.stem
    description = ""
    body = text
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        for line in fm.strip().splitlines():
            if line.lower().startswith("name:"):
                name = line.split(":", 1)[1].strip()
            elif line.lower().startswith("description:"):
                description = line.split(":", 1)[1].strip()
        body = body.strip()
    return Skill(name=name, description=description or name, body=body)


class SkillRegistry:
    def __init__(self, skills_dir: Path) -> None:
        self.dir = skills_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        defaults = {
            "zusammenfassen.md": (
                "---\nname: zusammenfassen\ndescription: Text prägnant zusammenfassen\n---\n"
                "Fasse den gegebenen Text in maximal fünf Stichpunkten zusammen. "
                "Nenne nur belegbare Aussagen, keine Interpretation."),
            "code-review.md": (
                "---\nname: code-review\ndescription: Code auf Fehler und Verbesserungen prüfen\n---\n"
                "Prüfe den Code auf Korrektheit, Sicherheitslücken und Vereinfachungen. "
                "Nenne konkrete Fundstellen und schlage Fixes vor."),
            "recherche.md": (
                "---\nname: recherche\ndescription: Strukturierte Kurzrecherche\n---\n"
                "Recherchiere das Thema, nenne 3-5 Kernpunkte und markiere Unsicherheiten "
                "klar als solche. Erfinde keine Quellen."),
            "projektplan.md": (
                "---\nname: projektplan\ndescription: Aufgabe in einen Umsetzungsplan zerlegen\n---\n"
                "Zerlege das Vorhaben in nummerierte Schritte mit klarer Definition of Done "
                "pro Schritt. Nenne Risiken und Abhängigkeiten."),
        }
        for fname, content in defaults.items():
            p = self.dir / fname
            if not p.exists():
                p.write_text(content, encoding="utf-8")

    def all(self) -> list[Skill]:
        return [_parse(p) for p in sorted(self.dir.glob("*.md"))]

    def get(self, name: str) -> Skill | None:
        for s in self.all():
            if s.name.lower() == name.lower():
                return s
        return None

    def apply(self, name: str, task: str) -> str:
        """Baut aus Skill + Aufgabe den finalen Prompt für das Gehirn."""
        skill = self.get(name)
        if skill is None:
            raise ValueError(f"Skill nicht gefunden: {name}")
        return f"# Skill: {skill.name}\n{skill.body}\n\n# Aufgabe\n{task}"
