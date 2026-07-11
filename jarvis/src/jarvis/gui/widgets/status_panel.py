"""Left instrument column: wordmark, clock, system stats, agents, activity feed."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from jarvis.gui import logic
from jarvis.gui.theme import Theme

_FEED_CAPACITY = 200


def _read_system_stats() -> list[str]:
    """Return CPU/RAM readout lines via psutil, or an empty list if unavailable."""
    try:
        import psutil
    except ImportError:
        return []
    try:
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        return [
            f"CPU  {cpu:5.1f} %",
            f"RAM  {memory.percent:5.1f} %  ({memory.used / 2**30:.1f} GiB)",
        ]
    except Exception:  # pragma: no cover - defensive against exotic platforms
        return []


class StatusPanel(QFrame):
    """Monospaced status readouts in the JARVIS instrument style.

    Sections: wordmark, live clock, system stats (omitted without psutil),
    subsystems/agents (via :meth:`set_status`) and a bounded scrolling
    activity feed (via :meth:`append_activity`).
    """

    def __init__(self, theme: Theme, assistant_name: str = "JARVIS", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._feed = logic.ActivityFeed(_FEED_CAPACITY)
        self.setObjectName("hudPanel")
        self.setMinimumWidth(230)
        self.setMaximumWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 14)
        layout.setSpacing(6)

        self._wordmark = QLabel(assistant_name.upper())
        self._wordmark.setObjectName("wordmark")
        self._clock = QLabel("--:--:--")
        self._clock.setObjectName("clock")
        self._date = QLabel("")
        self._date.setObjectName("dimText")

        self._stats_title = self._section("SYSTEM")
        self._stats = QLabel("")
        self._stats.setObjectName("dimText")
        self._agents_title = self._section("AGENTS")
        self._agents = QLabel("initialising...")
        self._agents.setObjectName("dimText")
        self._agents.setWordWrap(True)
        self._activity_title = self._section("ACTIVITY")
        self._activity = QPlainTextEdit()
        self._activity.setObjectName("activityFeed")
        self._activity.setReadOnly(True)
        self._activity.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._activity.setMaximumBlockCount(_FEED_CAPACITY)

        for widget in (
            self._wordmark,
            self._clock,
            self._date,
            self._stats_title,
            self._stats,
            self._agents_title,
            self._agents,
            self._activity_title,
        ):
            layout.addWidget(widget)
        layout.addWidget(self._activity, stretch=1)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()
        self._refresh()

    def _section(self, title: str) -> QLabel:
        label = QLabel(f"— {title} —")
        label.setObjectName("sectionTitle")
        label.setContentsMargins(0, 10, 0, 0)
        return label

    # -- live data --------------------------------------------------------------

    def _refresh(self) -> None:
        now = datetime.now()
        self._clock.setText(now.strftime("%H:%M:%S"))
        self._date.setText(now.strftime("%a %d %b %Y"))
        stats = _read_system_stats()
        self._stats_title.setVisible(bool(stats))
        self._stats.setVisible(bool(stats))
        if stats:
            self._stats.setText("\n".join(stats))

    def set_status(self, status: dict[str, Any]) -> None:
        """Display subsystems/agents from :meth:`JarvisApp.status` output."""
        agents = status.get("agents") or []
        subsystems = status.get("subsystems") or []
        lines = []
        if subsystems:
            lines.append("sys: " + ", ".join(str(s) for s in subsystems))
        lines.append("agt: " + (", ".join(str(a) for a in agents) or "core"))
        self._agents.setText("\n".join(lines))

    def append_activity(self, line: str) -> None:
        """Append one line to the scrolling activity feed (ring-buffered)."""
        stamped = f"{datetime.now():%H:%M:%S} {line}"
        self._feed.append(stamped)
        self._activity.appendPlainText(stamped)
        scrollbar = self._activity.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
