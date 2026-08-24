"""Ambient particle field: drifting points with faint plexus connections."""

from __future__ import annotations

import time

from PySide6.QtCore import QPointF, Qt, QTimer
from PySide6.QtGui import QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from jarvis.gui import logic
from jarvis.gui.theme import Theme

_PARTICLE_COUNT = 70
_CONNECT_DISTANCE = 130.0
_FIELD_FPS = 30  # background layer: half rate is plenty and saves CPU


class ParticleFieldWidget(QWidget):
    """Full-bleed background star field; pauses automatically while hidden."""

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._field = logic.ParticleField(_PARTICLE_COUNT, 800.0, 600.0)
        self._last_tick = time.monotonic()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._timer = QTimer(self)
        self._timer.setInterval(1000 // _FIELD_FPS)
        self._timer.timeout.connect(self._advance)
        self._timer.start()

    def _advance(self) -> None:
        now = time.monotonic()
        self._field.step(now - self._last_tick)
        self._last_tick = now
        self.update()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().resizeEvent(event)
        self._field.resize(float(self.width()), float(self.height()))

    def showEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().showEvent(event)
        self._last_tick = time.monotonic()
        self._timer.start()

    def hideEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().hideEvent(event)
        self._timer.stop()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        theme = self._theme
        particles = self._field.particles

        # Connective lines first, points on top.
        for i, j, strength in self._field.connections(_CONNECT_DISTANCE):
            pen = QPen(theme.with_alpha(theme.accent, int(46 * strength)), 1.0)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(particles[i].x, particles[i].y),
                QPointF(particles[j].x, particles[j].y),
            )

        painter.setPen(Qt.PenStyle.NoPen)
        for particle in particles:
            painter.setBrush(theme.with_alpha(theme.accent, 110))
            painter.drawEllipse(
                QPointF(particle.x, particle.y), particle.size / 2.0, particle.size / 2.0
            )
