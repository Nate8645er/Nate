"""The arc reactor: concentric animated HUD rings with a glowing core."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPaintEvent, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

from jarvis.gui import logic
from jarvis.gui.theme import Theme


@dataclass(slots=True)
class _RingSpec:
    """Geometry and motion of one reactor ring."""

    radius: float  # fraction of the widget radius
    width: float  # pen width in px
    speed: float  # degrees per second (sign = direction)
    style: str  # "ticks" | "arcs" | "dashed" | "solid"
    color: str  # "accent" | "secondary"
    alpha: int  # base opacity 0..255


_RINGS: tuple[_RingSpec, ...] = (
    _RingSpec(radius=0.96, width=1.4, speed=9.0, style="ticks", color="accent", alpha=170),
    _RingSpec(radius=0.84, width=3.0, speed=-16.0, style="arcs", color="secondary", alpha=200),
    _RingSpec(radius=0.70, width=1.8, speed=26.0, style="dashed", color="accent", alpha=190),
    _RingSpec(radius=0.56, width=1.0, speed=-40.0, style="solid", color="accent", alpha=120),
)

_TICK_COUNT = 60
_ARC_SEGMENTS = 3
_ARC_SPAN = 42.0  # degrees per gold arc segment


class ArcReactorWidget(QWidget):
    """Iron-Man style arc reactor with voice-reactive core glow and ring speed.

    The ``level`` property (0..1) feeds both the core brightness and a rotation
    boost; it decays smoothly so short spikes leave a visible afterglow.
    """

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._angles: list[float] = [0.0] * len(_RINGS)
        self._level = 0.0
        self._target_level = 0.0
        self._last_tick = time.monotonic()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(180, 180)
        self._timer = QTimer(self)
        self._timer.setInterval(max(1000 // theme.fps, 8))
        self._timer.timeout.connect(self._advance)
        self._timer.start()

    # -- voice reactivity -----------------------------------------------------------

    @property
    def level(self) -> float:
        """Current smoothed voice level (0..1)."""
        return self._level

    @level.setter
    def level(self, value: float) -> None:
        self._target_level = logic.clamp(value)

    def set_level(self, value: float) -> None:
        """Slot-friendly setter for :attr:`level`."""
        self.level = value

    # -- animation ------------------------------------------------------------------

    def _advance(self) -> None:
        now = time.monotonic()
        dt = min(now - self._last_tick, 0.25)
        self._last_tick = now
        self._level = logic.smooth_level(self._level, self._target_level)
        for index, spec in enumerate(_RINGS):
            self._angles[index] = logic.advance_angle(
                self._angles[index], spec.speed, dt, boost=self._level
            )
        self.update()

    def showEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().showEvent(event)
        self._last_tick = time.monotonic()
        self._timer.start()

    def hideEvent(self, event) -> None:  # noqa: N802 - Qt override
        super().hideEvent(event)
        self._timer.stop()

    # -- painting -------------------------------------------------------------------

    def _ring_color(self, spec: _RingSpec) -> QColor:
        base = self._theme.accent if spec.color == "accent" else self._theme.secondary
        boosted = min(spec.alpha + int(70 * self._level), 255)
        return self._theme.with_alpha(base, boosted)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 - Qt override
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = self.rect().center()
        radius = min(self.width(), self.height()) / 2.0 - 6.0
        if radius <= 10:
            return
        painter.translate(center)

        self._paint_core(painter, radius)
        for index, spec in enumerate(_RINGS):
            painter.save()
            painter.rotate(self._angles[index])
            self._paint_ring(painter, spec, radius * spec.radius)
            painter.restore()

    def _paint_core(self, painter: QPainter, radius: float) -> None:
        """Radial-gradient core: white-hot centre, cyan falloff, additive glow."""
        theme = self._theme
        core_radius = radius * (0.30 + 0.06 * self._level)
        glow = QRadialGradient(0.0, 0.0, core_radius * 1.9)
        intensity = 0.55 + 0.45 * self._level
        glow.setColorAt(0.0, theme.with_alpha(QColor(235, 250, 255), int(235 * intensity)))
        glow.setColorAt(0.25, theme.with_alpha(theme.accent, int(210 * intensity)))
        glow.setColorAt(0.62, theme.with_alpha(theme.accent, int(70 * intensity)))
        glow.setColorAt(1.0, theme.with_alpha(theme.accent, 0))
        painter.save()
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(
            QRectF(-core_radius * 1.9, -core_radius * 1.9, core_radius * 3.8, core_radius * 3.8)
        )
        painter.restore()
        # Thin containment ring around the core.
        pen = QPen(theme.with_alpha(theme.accent, 200), 1.2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(-core_radius, -core_radius, core_radius * 2, core_radius * 2))

    def _paint_ring(self, painter: QPainter, spec: _RingSpec, ring_radius: float) -> None:
        color = self._ring_color(spec)
        pen = QPen(color, spec.width)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(-ring_radius, -ring_radius, ring_radius * 2, ring_radius * 2)

        if spec.style == "ticks":
            painter.setPen(pen)
            inner = ring_radius - 7.0
            for tick in range(_TICK_COUNT):
                angle = tick / _TICK_COUNT * math.tau
                length = inner - (5.0 if tick % 5 == 0 else 0.0)
                painter.drawLine(
                    int(math.cos(angle) * length),
                    int(math.sin(angle) * length),
                    int(math.cos(angle) * ring_radius),
                    int(math.sin(angle) * ring_radius),
                )
        elif spec.style == "arcs":
            painter.setPen(pen)
            step = 360.0 / _ARC_SEGMENTS
            for segment in range(_ARC_SEGMENTS):
                start = segment * step
                painter.drawArc(rect, int(start * 16), int(_ARC_SPAN * 16))
        elif spec.style == "dashed":
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern([6.0, 4.0])
            painter.setPen(pen)
            painter.drawEllipse(rect)
        else:  # solid
            painter.setPen(pen)
            painter.drawEllipse(rect)
