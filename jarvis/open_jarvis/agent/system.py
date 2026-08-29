"""JARVIS-Systemzusammenbau — die Systemarchitektur als lauffaehiges Ganzes.

Setzt die Bausteine des Architektur-Diagramms zu EINEM System zusammen:

    Nutzer -> Sprache-zu-Text -> Systemprompt (Persoenlichkeit)
           -> GEHIRN (Fable 5) denkt -> Aktions-System (Agent + Werkzeuge)
           -> Sprachausgabe (TTS) -> Antwort an den Nutzer

Das Gehirn ist **Fable 5** (nicht Haiku). Ohne API-Schluessel plant der lokale
Motor weiter — das System bleibt jederzeit bedienbar.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from open_jarvis.agent.agent import DEFAULT_WORKSPACE, AgentRun, JarvisAgent
from open_jarvis.agent.models import AgentModel, brain_model, resolve_model

# --------------------------------------------------------------------------- #
# Systemprompt / Persoenlichkeit ("sozusagen die Persoenlichkeit von JARVIS
# und seine Anweisungen" — der lila Kasten im Architektur-Diagramm).
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = (
    "Du bist J.A.R.V.I.S., der persoenliche KI-Assistent des Nutzers. "
    "Du bist zuvorkommend, praezise und proaktiv. Du sprichst Deutsch, hoeflich "
    "und knapp, und redest den Nutzer mit 'Sir' an. Du planst Aufgaben, nutzt die "
    "verfuegbaren Werkzeuge und meldest klar, was du getan hast. Wenn dir etwas "
    "fehlt (z. B. ein Schluessel), sagst du es ehrlich."
)

#: Kurze Bestaetigungen, mit denen JARVIS eine Antwort einleitet (deterministisch
#: je nach Ergebnis gewaehlt — kein Zufall, damit Tests stabil bleiben).
_ACK_OK = "Sehr wohl, Sir."
_ACK_INFO = "Zu Ihren Diensten, Sir."
_ACK_FAIL = "Verzeihung, Sir."


def architecture() -> dict[str, Any]:
    """Die Systemarchitektur als strukturierte Daten (Single Source of Truth).

    Spiegelt das Whiteboard-Diagramm; das Gehirn ist explizit Fable 5.
    """

    brain = brain_model()
    return {
        "title": "JARVIS — Systemarchitektur",
        "subtitle": "Persoenlicher KI-Assistent mit Sprachsteuerung",
        "brain": {"label": brain.label, "model_id": brain.model_id, "role": "Gehirn (denkt/plant/entscheidet)"},
        "layers": [
            {
                "name": "Chrome Browser",
                "components": [
                    {"name": "Sprache zu Text", "detail": "Web Speech API"},
                    {"name": "JARVIS Orb UI", "detail": "Arc-Reactor-Kern"},
                    {"name": "Audio-Ausgabe", "detail": "Sprachantwort"},
                ],
            },
            {
                "name": "Lokaler Server (Bridge)",
                "components": [
                    {"name": "Systemprompt", "detail": "Persoenlichkeit + Anweisungen"},
                    {"name": "Sprachausgabe", "detail": "Text -> Stimme"},
                    {"name": "Aktions-System", "detail": "Agent + Werkzeuge"},
                ],
            },
            {
                "name": "Externe Services",
                "components": [
                    {"name": f"Claude AI — {brain.label}", "detail": "GEHIRN — denkt/plant/entscheidet"},
                    {"name": "Text-to-Speech", "detail": "Browser-TTS / ElevenLabs"},
                ],
            },
            {
                "name": "Lokale Tools",
                "components": [
                    {"name": "Browser-Steuerung", "detail": "Playwright"},
                    {"name": "Bildschirm sehen", "detail": "Claude Vision"},
                    {"name": "Shopify", "detail": "Produkte, Rabatte, Analytics"},
                ],
            },
        ],
        "flow": [
            "Nutzer spricht",
            "Sprache-zu-Text",
            "Systemprompt",
            f"{brain.label} denkt",
            "Aktions-System fuehrt Werkzeuge aus",
            "Text-to-Speech",
            "Antwort an den Nutzer",
        ],
    }


@dataclass
class SystemResponse:
    """Antwort des JARVIS-Systems auf einen Befehl."""

    command: str
    brain: str
    spoken: str
    run: AgentRun
    field_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = self.run.to_dict()
        data.update({"command": self.command, "brain": self.brain, "spoken": self.spoken})
        return data


def _voice(run: AgentRun) -> str:
    """Formuliert die Agent-Antwort in JARVIS-Persoenlichkeit (fuer die Stimme)."""

    final = run.plan.final or "Erledigt."
    if not run.ok:
        return f"{_ACK_FAIL} {final}"
    if run.execute and any(o.result.executed for o in run.outcomes):
        return f"{_ACK_OK} {final}"
    return f"{_ACK_INFO} {final}"


class JarvisSystem:
    """Die zusammengesetzte JARVIS-Systemarchitektur als lauffaehiges Objekt."""

    def __init__(
        self,
        *,
        model: AgentModel | str | None = None,
        workspace: Path | str = DEFAULT_WORKSPACE,
        execute: bool = False,
        system_prompt: str = SYSTEM_PROMPT,
    ) -> None:
        # Standard-Gehirn = Fable 5 (nicht Haiku).
        self.model = model if isinstance(model, AgentModel) else (resolve_model(model) if model else brain_model())
        self.workspace = Path(workspace)
        self.execute = execute
        self.system_prompt = system_prompt

    @property
    def brain(self) -> AgentModel:
        return self.model

    def architecture(self) -> dict[str, Any]:
        return architecture()

    def handle(self, command: str, *, execute: bool | None = None) -> SystemResponse:
        """Einen Befehl durch das komplette System schicken (denken -> handeln -> antworten)."""

        do_exec = self.execute if execute is None else execute
        agent = JarvisAgent(model=self.model, workspace=self.workspace, execute=do_exec)
        run = agent.run(command)
        return SystemResponse(
            command=command,
            brain=self.model.label,
            spoken=_voice(run),
            run=run,
        )
