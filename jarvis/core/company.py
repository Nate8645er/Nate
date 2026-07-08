"""Das virtuelle Unternehmen (ULTRA AI ENTERPRISE OS) in Jarvis.

Der Befehl /firma schickt eine Aufgabe durch die Abteilungen (Agenten).
Jede Abteilung sieht die Aufgabe und die Ergebnisse der vorherigen
Abteilungen und liefert ihren eigenen Beitrag.

Zwei Betriebsarten (config.json, company.pipeline):
  * Liste von Abteilungen - feste Reihenfolge, wie bisher.
  * "auto" - der Orchestrator wählt pro Aufgabe die passenden
    Abteilungen aus (2 bis 5), und der CEO fasst am Ende alles zu
    einer Entscheidung zusammen. So arbeitet der ganze Konzern, ohne
    dass für jede Frage alle 20 Abteilungen anrücken müssen.
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

#: Bei pipeline "auto": maximal so viele Fach-Abteilungen pro Aufgabe
AUTO_MAX_DEPARTMENTS = 5
#: Bei pipeline "auto": diese Rolle fasst am Ende alles zusammen
FINAL_ROLE = "ultra-ceo"
#: Bei pipeline "auto": diese Rolle wählt die Abteilungen aus
PLANNER_ROLE = "ultra-orchestrator"


class Company:
    """Orchestriert mehrere Agenten zu einem virtuellen Unternehmen."""

    def __init__(
        self,
        client: OllamaClient,
        agents: AgentRegistry,
        pipeline: list[str] | str | None = None,
    ):
        self.client = client
        self.agents = agents
        self.pipeline = pipeline or DEFAULT_PIPELINE

    def _select_departments(self, task: str) -> list[str]:
        """Auto-Modus: Der Orchestrator wählt die passenden Abteilungen."""
        candidates = [
            name for name in self.agents.agents
            if name not in (PLANNER_ROLE, FINAL_ROLE)
        ]
        if not candidates:
            return DEFAULT_PIPELINE
        catalog = "\n".join(
            f"- {name}: {' '.join(str(meta.get('description', '')).split())[:120]}"
            for name, (meta, _) in self.agents.agents.items()
            if name in candidates
        )
        question = (
            f"AUFGABE:\n{task}\n\n"
            f"VERFÜGBARE ABTEILUNGEN:\n{catalog}\n\n"
            f"Wähle die 2 bis {AUTO_MAX_DEPARTMENTS} Abteilungen, die für "
            "diese Aufgabe wirklich gebraucht werden, in sinnvoller "
            "Arbeitsreihenfolge. Antworte NUR mit den Namen, durch Kommas "
            "getrennt, ohne Erklärung."
        )
        try:
            answer = self.agents.ask(self.client, PLANNER_ROLE, question)
        except Exception as e:  # noqa: BLE001 - Auswahl darf nie alles stoppen
            logger.warning("Abteilungs-Auswahl fehlgeschlagen (%s).", e)
            return DEFAULT_PIPELINE
        chosen = []
        for token in answer.replace("\n", ",").split(","):
            name = token.strip().strip("-•* ").lower()
            if name in self.agents.agents and name not in chosen:
                chosen.append(name)
        chosen = chosen[:AUTO_MAX_DEPARTMENTS]
        if not chosen:
            logger.warning("Auswahl unlesbar ('%s') - nutze Standard.", answer[:80])
            return DEFAULT_PIPELINE
        logger.info("Auto-Pipeline: %s", " -> ".join(chosen))
        return chosen

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
        if self.pipeline == "auto":
            pipeline = self._select_departments(task)
            if FINAL_ROLE in self.agents.agents and FINAL_ROLE not in pipeline:
                pipeline = pipeline + [FINAL_ROLE]
        else:
            pipeline = list(self.pipeline)

        available = [r for r in pipeline if r in self.agents.agents]
        missing = [r for r in pipeline if r not in self.agents.agents]
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
