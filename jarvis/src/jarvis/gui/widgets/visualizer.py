"""Circular voice visualizer: a ring of spectrum bars around the reactor."""

from __future__ import annotations

import math
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from jarvis.gui import logic
from jarvis.gui.theme import Theme

_BAR_COUNT = 48


class VoiceVisualizerWidget(QWidget):
    """Radial bar spectrum fed by voice levels, breathing gently when idle.

    Feed it either a single loudness via :meth:`set_level` (expanded into a
    shimmering pseudo-spectrum) or real magnitudes via :meth:`set_spectrum`.
    Bars rise fast and decay slowly (see :func:`jarvis.gui.logic.decay_spectrum`).
    """

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._bars: list[float] = [0.0] * _BAR_COUNT
        self._targets: list[float] = [0.0] * _BAR_COUNT
        self._level = 0.0
        self._last_input = 0.0  # monotonic time of the last external signal
        self._start = time.monotonic()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setMinimumSize(220, 220)
        self._timer = QTimer(self)
        self._timer.setInterval(max(1000 // theme.fps, 8))
        self._timer.timeout.connect(self._advance)
        self._timer.start()

    # -- input ----------------------------------------------------------------------

    def set_level(self, level: float) -> None:
        """Drive the ring from a single loudness value (0..1)."""
        self._level = logic.clamp(level)
        self._last_input = time.monotonic()

    def set_spectrum(self, spectrum: list[float]) -> None:
        """Drive the ring from real spectrum magnitudes (any length, 0..1)."""
        self._targets = logic.resample(list(spectrum), _BAR_COUNT)
        self._level = max(self._targets, default=0.0)
        self._last_input = time.monotonic()

    # -- animation ------------------------------------------------------------------

    def _advance(self) -> None:
        now = time.monotonic()
        t = now - self._start
        idle = now - self._last_input > 1.2
        if idle:
            # Idle breathing: a soft sine floor so the HUD never looks dead.
            self._targets = logic.spread_level(logic.breathing(t), _BAR_COUNT, t * 0.35)
        elif self._level > 0.0:
            self._targets = logic.spread_level(self._level, _BAR_COUNT, t)
        self._bars = logic.decay_spectrum(self._bars, self._targets)
        self.update()

    def showEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().showEvent(event)
        self._timer.start()

    def hideEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().hideEvent(event)
        self._timer.stop()

    # -- painting -------------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = self.rect().center()
        radius = min(self.width(), self.height()) / 2.0 - 3.0
        if radius <= 20:
            return
        painter.translate(center)

        inner = radius * 0.80  # bars live in the outer annulus, clear of the reactor
        max_len = radius - inner - 2.0
        theme = self._theme
        for index, value in enumerate(self._bars):
            angle = index / _BAR_COUNT * math.tau - math.pi / 2.0
            length = 1.5 + value * max_len
            alpha = int(60 + 195 * value)
            pen = QPen(theme.with_alpha(theme.accent, alpha), 2.4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            painter.drawLine(
                int(cos_a * inner),
                int(sin_a * inner),
                int(cos_a * (inner + length)),
                int(sin_a * (inner + length)),
            )
