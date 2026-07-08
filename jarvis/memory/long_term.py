"""Langzeitgedächtnis: Fakten, die über Sitzungen hinweg erhalten bleiben.

Die Fakten werden als JSON in data/memory/long_term.json gespeichert und
bei jedem Gespräch automatisch in den System-Prompt von Jarvis eingebaut -
so "erinnert" sich das Modell dauerhaft an dich.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("jarvis.memory")


class LongTermMemory:
    """Speichert und verwaltet dauerhafte Fakten über den Nutzer."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.facts: list[dict] = []
        self._load()

    def _load(self) -> None:
        if not self.file_path.exists():
            logger.info("Noch kein Langzeitgedächtnis vorhanden (%s).",
                        self.file_path)
            return
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
            self.facts = data.get("facts", [])
            logger.info("Langzeitgedächtnis geladen: %d Fakt(en).",
                        len(self.facts))
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Langzeitgedächtnis konnte nicht geladen werden: %s", e)
            self.facts = []

    def _save(self) -> None:
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text(
                json.dumps({"facts": self.facts}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            logger.error("Langzeitgedächtnis konnte nicht gespeichert werden: %s", e)

    def remember(self, fact: str) -> int:
        """Speichert einen Fakt dauerhaft. Gibt seine Nummer zurück."""
        self.facts.append({
            "text": fact.strip(),
            "created": datetime.now().isoformat(timespec="seconds"),
        })
        self._save()
        logger.info("Neuer Fakt gespeichert: %s", fact.strip())
        return len(self.facts)

    def forget(self, number: int) -> str | None:
        """Löscht den Fakt mit der angegebenen Nummer (1-basiert)."""
        if 1 <= number <= len(self.facts):
            removed = self.facts.pop(number - 1)
            self._save()
            logger.info("Fakt vergessen: %s", removed["text"])
            return removed["text"]
        return None

    def forget_all(self) -> int:
        """Löscht das komplette Langzeitgedächtnis. Gibt die Anzahl zurück."""
        count = len(self.facts)
        self.facts = []
        self._save()
        logger.info("Langzeitgedächtnis komplett gelöscht (%d Fakten).", count)
        return count

    def overview(self) -> str:
        """Nummerierte Liste aller Fakten für /gedaechtnis."""
        if not self.facts:
            return "Das Langzeitgedächtnis ist leer. Speichere Fakten mit: /merken <fakt>"
        lines = [
            f"{i}. {fact['text']}  (gespeichert am {fact['created'][:10]})"
            for i, fact in enumerate(self.facts, start=1)
        ]
        return "\n".join(lines)

    def as_prompt_context(self) -> str:
        """Baut den Gedächtnis-Block für den System-Prompt."""
        if not self.facts:
            return ""
        lines = "\n".join(f"- {fact['text']}" for fact in self.facts)
        return (
            "\n\nDauerhaft gespeicherte Fakten über deinen Nutzer "
            "(nutze sie, wenn sie relevant sind):\n" + lines
        )
