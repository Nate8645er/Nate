"""Misst pro Gesprächsrunde, wohin die Zeit geht.

Erst messen, dann optimieren: Der TurnTimer startet in dem Moment, in dem
die Aufnahme endet (der Nutzer also fertig gesprochen hat), und sammelt
danach benannte Zwischenzeiten - z.B. "Transkript", "erster Satz",
"Sprachbeginn". So sieht man pro Runde, welcher Schritt die Wartezeit
verursacht.
"""

import logging
import time

logger = logging.getLogger("jarvis.latency")


class TurnTimer:
    """Zwischenzeiten einer Gesprächsrunde, relativ zum Ende der Aufnahme."""

    def __init__(self):
        self._t0: float | None = None
        self._marks: dict[str, float] = {}

    def start(self) -> None:
        """Nullpunkt setzen: der Nutzer hat gerade aufgehört zu sprechen."""
        self._t0 = time.monotonic()
        self._marks.clear()

    def mark(self, name: str) -> None:
        """Zwischenzeit festhalten. Nur der erste Aufruf pro Name zählt."""
        if self._t0 is None or name in self._marks:
            return
        self._marks[name] = time.monotonic() - self._t0

    def report(self) -> str:
        """Kompakte Übersicht, z.B. 'Transkript 0.8s · erster Satz 1.4s'."""
        if not self._marks:
            return ""
        return " · ".join(
            f"{name} {seconds:.1f}s" for name, seconds in self._marks.items()
        )

    def log(self) -> None:
        """Schreibt die Übersicht ins Log (für spätere Vergleiche)."""
        text = self.report()
        if text:
            logger.info("Latenz: %s", text)
