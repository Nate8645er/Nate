"""Das virtuelle Unternehmen (ULTRA AI ENTERPRISE OS) in Jarvis.

Der Befehl /firma schickt eine Aufgabe nacheinander durch die konfigurierten
Abteilungen (Agenten). Jede Abteilung sieht die Aufgabe und die Ergebnisse
der vorherigen Abteilungen und liefert ihren eigenen Beitrag.

Pipeline (konfigurierbar in config.json unter company.pipeline), Standard:
  1. ultra-orchestrator - zerlegt die Aufgabe in einen Ausführungsplan
  2. ultra-architect    - entwirft die technische Lösung
  3. ultra-fullstack    - beschreibt/liefert die Umsetzung
  4. ultra-qa           - prüft das Ergebnis kritisch
"""

import logging
from collections.abc import Callable

from jarvis.core.agents import AgentRegistry
from jarvis.core.ollama_client import OllamaClient

logger = logging.getLogger("jarvis.company")

DEFAULT_PIPELINE = [
    "ultra-orchestrator",
    "ultra-architect",
    "ultra-fullstack",
    "ultra-qa",
]


class Company:
    """Orchestriert mehrere Agenten zu einem virtuellen Unternehmen."""

    def __init__(
        self,
        client: OllamaClient,
        agents: AgentRegistry,
        pipeline: list[str] | None = None,
    ):
        self.client = client
        self.agents = agents
        self.pipeline = pipeline or DEFAULT_PIPELINE

    def run(
        self,
        task: str,
        on_step: Callable[[str, int, int], None] | None = None,
    ) -> list[tuple[str, str]]:
        """Führt die Aufgabe durch alle Abteilungen. Ergebnis: [(rolle, beitrag)].

        Args:
            task: Die Aufgabe des Nutzers.
            on_step: Optionaler Callback (rolle, schritt, gesamt) für
                Fortschrittsanzeige, da lokale Modelle etwas brauchen.
        """
        available = [r for r in self.pipeline if r in self.agents.agents]
        missing = [r for r in self.pipeline if r not in self.agents.agents]
        if missing:
            logger.warning("Abteilungen nicht gefunden: %s", ", ".join(missing))
        if not available:
            return [("fehler", "Keine der konfigurierten Abteilungen wurde gefunden.")]

        results: list[tuple[str, str]] = []
        for index, role in enumerate(available, start=1):
            if on_step:
                on_step(role, index, len(available))
            question = self._build_question(task, results)
            answer = self.agents.ask(self.client, role, question)
            results.append((role, answer))
            logger.info("Abteilung '%s' hat geliefert (%d Zeichen).",
                        role, len(answer))
        return results

    @staticmethod
    def _build_question(task: str, previous: list[tuple[str, str]]) -> str:
        """Baut die Anfrage: Aufgabe + bisherige Beiträge der Abteilungen."""
        parts = [f"AUFGABE:\n{task}"]
        if previous:
            parts.append(
                "\nBISHERIGE BEITRÄGE DEINER KOLLEGEN "
                "(baue darauf auf, wiederhole nichts unnötig):"
            )
            for role, answer in previous:
                parts.append(f"\n--- Beitrag von {role} ---\n{answer}")
            parts.append(
                "\nLiefere jetzt deinen eigenen Beitrag aus Sicht deiner Rolle."
            )
        return "\n".join(parts)
