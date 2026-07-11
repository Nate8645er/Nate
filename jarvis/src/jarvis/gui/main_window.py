"""JARVIS main window: frameless translucent HUD with responsive layout.

Layering (back to front): particle field (full bleed) -> content grid with
status panel (left), HUD stack (arc reactor inside voice visualizer, centre)
and chat panel (right). Below the width threshold the chat column drops
underneath the HUD so the reactor always keeps centre stage.
"""

from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QIcon,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPixmap,
    QRadialGradient,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QMainWindow,
    QMenu,
    QSystemTrayIcon,
    QWidget,
)

from jarvis.core.config import JarvisConfig
from jarvis.gui import logic
from jarvis.gui.theme import Theme
from jarvis.gui.widgets.arc_reactor import ArcReactorWidget
from jarvis.gui.widgets.chat_panel import ChatPanel
from jarvis.gui.widgets.particles import ParticleFieldWidget
from jarvis.gui.widgets.status_panel import StatusPanel
from jarvis.gui.widgets.visualizer import VoiceVisualizerWidget


class BridgeLike(Protocol):
    """Duck-typed bridge contract, so tests can wire a stub without JarvisApp."""

    delta: Any
    answer: Any
    event: Any
    level: Any
    started: Any
    error: Any

    def send_text(self, text: str) -> None:
        """Submit a user request."""


def render_reactor_icon(theme: Theme, size: int = 64) -> QIcon:
    """Draw the window/tray icon programmatically (no asset files)."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    center = size / 2.0
    core = size * 0.22
    gradient = QRadialGradient(center, center, size * 0.48)
    gradient.setColorAt(0.0, QColor(240, 252, 255))
    gradient.setColorAt(0.35, theme.accent)
    gradient.setColorAt(1.0, theme.with_alpha(theme.accent, 0))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(gradient)
    painter.drawEllipse(QRectF(size * 0.04, size * 0.04, size * 0.92, size * 0.92))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(theme.with_alpha(theme.accent, 230))
    painter.drawEllipse(QRectF(center - core, center - core, core * 2, core * 2))
    painter.setPen(theme.with_alpha(theme.secondary, 200))
    ring = size * 0.36
    painter.drawEllipse(QRectF(center - ring, center - ring, ring * 2, ring * 2))
    painter.end()
    return QIcon(pixmap)


class _HudStack(QWidget):
    """Overlays the arc reactor centred inside the full-bleed voice visualizer."""

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.visualizer = VoiceVisualizerWidget(theme, self)
        self.reactor = ArcReactorWidget(theme, self)
        self.setMinimumSize(280, 280)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 - Qt override
        super().resizeEvent(event)
        side = min(self.width(), self.height())
        x = (self.width() - side) // 2
        y = (self.height() - side) // 2
        self.visualizer.setGeometry(x, y, side, side)
        reactor_side = int(side * 0.72)
        offset = (side - reactor_side) // 2
        self.reactor.setGeometry(x + offset, y + offset, reactor_side, reactor_side)


class JarvisMainWindow(QMainWindow):
    """Frameless, translucent, draggable HUD window wired to a JarvisBridge."""

    def __init__(
        self,
        config: JarvisConfig,
        bridge: BridgeLike,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._bridge = bridge
        self._theme = Theme.from_config(config.gui)
        self._drag_offset: QPoint | None = None
        self._mode = ""

        self._configure_window()
        self._build_ui()
        self._wire_bridge()
        self._setup_tray()
        self._place_on_monitor()
        self._apply_layout(logic.layout_mode(self.width()))

    # -- window chrome ---------------------------------------------------------------

    def _configure_window(self) -> None:
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        if self._config.gui.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(logic.clamp(self._config.gui.transparency, 0.3, 1.0))
        self.setWindowTitle(self._config.assistant_name)
        self.setWindowIcon(render_reactor_icon(self._theme))
        self.setMinimumSize(720, 480)
        self.resize(1280, 760)
        self.setStyleSheet(self._theme.stylesheet())

    def _place_on_monitor(self) -> None:
        screens = QApplication.screens()
        index = self._config.gui.monitor_index
        screen = screens[index] if 0 <= index < len(screens) else QApplication.primaryScreen()
        if screen is not None:
            geometry = screen.availableGeometry()
            self.move(geometry.center() - self.rect().center())

    def _setup_tray(self) -> None:
        self._tray: QSystemTrayIcon | None = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray = QSystemTrayIcon(render_reactor_icon(self._theme), self)
        menu = QMenu(self)
        menu.addAction("Show HUD", self.showNormal)
        menu.addSeparator()
        menu.addAction("Quit", QApplication.quit)
        self._tray.setContextMenu(menu)
        self._tray.setToolTip(self._config.assistant_name)
        self._tray.show()

    # -- layout -----------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("hudRoot")
        root.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        root.setStyleSheet(
            "#hudRoot { background-color: rgba(6, 10, 18, 0.88); "
            "border: 1px solid rgba(40, 200, 255, 0.30); border-radius: 16px; }"
        )
        self.setCentralWidget(root)

        self._particles = ParticleFieldWidget(self._theme, root)
        self._particles.lower()

        self._status = StatusPanel(self._theme, self._config.assistant_name, root)
        self._hud = _HudStack(self._theme, root)
        self._chat = ChatPanel(self._theme, root)
        self._chat.setMaximumWidth(430)

        self._grid = QGridLayout(root)
        self._grid.setContentsMargins(20, 20, 20, 20)
        self._grid.setSpacing(16)

    def _apply_layout(self, mode: str) -> None:
        """Re-seat the three columns for ``"wide"`` or ``"narrow"`` mode."""
        if mode == self._mode:
            return
        self._mode = mode
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(self.centralWidget())
        if mode == "wide":
            self._grid.addWidget(self._status, 0, 0)
            self._grid.addWidget(self._hud, 0, 1)
            self._grid.addWidget(self._chat, 0, 2)
            self._grid.setColumnStretch(0, 0)
            self._grid.setColumnStretch(1, 1)
            self._grid.setColumnStretch(2, 0)
            self._grid.setRowStretch(0, 1)
            self._grid.setRowStretch(1, 0)
            self._chat.setMaximumWidth(430)
        else:  # narrow: chat drops below the HUD, spanning status + centre
            self._grid.addWidget(self._status, 0, 0)
            self._grid.addWidget(self._hud, 0, 1)
            self._grid.addWidget(self._chat, 1, 0, 1, 2)
            self._grid.setColumnStretch(0, 0)
            self._grid.setColumnStretch(1, 1)
            self._grid.setColumnStretch(2, 0)
            self._grid.setRowStretch(0, 3)
            self._grid.setRowStretch(1, 2)
            self._chat.setMaximumWidth(16_777_215)
        for widget in (self._status, self._hud, self._chat):
            widget.show()
        self._particles.lower()

    # -- bridge wiring ------------------------------------------------------------------

    def _wire_bridge(self) -> None:
        bridge = self._bridge
        bridge.delta.connect(self._chat.append_delta)
        bridge.answer.connect(self._chat.finish_assistant)
        bridge.level.connect(self._on_level)
        bridge.event.connect(self._on_event)
        bridge.started.connect(self._on_started)
        bridge.error.connect(self._on_error)
        self._chat.message_submitted.connect(bridge.send_text)

    def _on_level(self, level: float) -> None:
        self._hud.reactor.set_level(level)
        self._hud.visualizer.set_level(level)

    def _on_event(self, topic: str, data: object) -> None:
        payload = data if isinstance(data, dict) else {}
        line = logic.format_event(topic, payload)
        if line is not None:
            self._status.append_activity(line)

    def _on_started(self, status: object) -> None:
        if isinstance(status, dict):
            self._status.set_status(status)
        self._status.append_activity("all systems nominal")

    def _on_error(self, message: str) -> None:
        self._chat.add_system_message(message)
        self._status.append_activity(f"error: {message}")

    # -- interaction ---------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt override
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt override
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt override
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt override
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 - Qt override
        super().resizeEvent(event)
        central = self.centralWidget()
        if central is not None:
            self._particles.setGeometry(central.rect())
        self._apply_layout(logic.layout_mode(self.width()))
