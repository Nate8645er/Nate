"""Chat column: message bubbles with streaming assistant output."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from jarvis.gui.theme import Theme


class ChatPanel(QFrame):
    """Message list plus input row.

    User messages sit right (cyan-tinted), assistant messages left. Streaming
    works via :meth:`begin_assistant` / :meth:`append_delta` /
    :meth:`finish_assistant`; a lone ``...`` acts as the typing indicator.
    """

    message_submitted = Signal(str)

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._current: QLabel | None = None  # streaming assistant bubble
        self.setObjectName("hudPanel")
        self.setMinimumWidth(300)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("chatScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        self._messages = QVBoxLayout(container)
        self._messages.setContentsMargins(2, 2, 2, 2)
        self._messages.setSpacing(6)
        self._messages.addStretch(1)
        self._scroll.setWidget(container)
        root.addWidget(self._scroll, stretch=1)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self._entry = QLineEdit()
        self._entry.setPlaceholderText("Ask JARVIS...")
        self._entry.returnPressed.connect(self._submit)
        self._send = QPushButton("SEND")
        self._send.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send.clicked.connect(self._submit)
        input_row.addWidget(self._entry, stretch=1)
        input_row.addWidget(self._send)
        root.addLayout(input_row)

    # -- sending ----------------------------------------------------------------

    def _submit(self) -> None:
        text = self._entry.text().strip()
        if not text:
            return
        self._entry.clear()
        self.add_user_message(text)
        self.begin_assistant()
        self.message_submitted.emit(text)

    # -- message construction -----------------------------------------------------

    def _add_bubble(self, text: str, object_name: str, align_right: bool) -> QLabel:
        bubble = QLabel(text)
        bubble.setObjectName(object_name)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setMaximumWidth(int(self.width() * 0.85) or 380)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if align_right:
            row.addStretch(1)
            row.addWidget(bubble)
        else:
            row.addWidget(bubble)
            row.addStretch(1)
        # Insert above the trailing stretch item.
        self._messages.insertLayout(self._messages.count() - 1, row)
        QTimer.singleShot(0, self._scroll_to_bottom)
        return bubble

    def _scroll_to_bottom(self) -> None:
        scrollbar = self._scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def add_user_message(self, text: str) -> None:
        """Append a right-aligned, cyan-tinted user bubble."""
        self._add_bubble(text, "userBubble", align_right=True)

    def add_system_message(self, text: str) -> None:
        """Append a small centred system/notice line (e.g. errors)."""
        bubble = self._add_bubble(text, "systemBubble", align_right=False)
        bubble.setAlignment(Qt.AlignmentFlag.AlignHCenter)

    def begin_assistant(self) -> None:
        """Open a streaming assistant bubble showing a typing indicator."""
        if self._current is None:
            self._current = self._add_bubble("...", "assistantBubble", align_right=False)

    def append_delta(self, delta: str) -> None:
        """Stream one text delta into the open assistant bubble."""
        if self._current is None:
            self.begin_assistant()
        assert self._current is not None
        text = self._current.text()
        if text == "...":
            text = ""
        self._current.setText(text + delta)
        self._scroll_to_bottom()

    def finish_assistant(self, text: str) -> None:
        """Finalise the streaming bubble with the definitive answer text."""
        if self._current is None and text:
            self.begin_assistant()
        if self._current is not None:
            self._current.setText(text or self._current.text())
            self._current = None
        self._scroll_to_bottom()
