"""The asyncio <-> Qt bridge.

:class:`JarvisBridge` owns a background thread running an asyncio event loop
in which :class:`~jarvis.app.JarvisApp` lives. GUI-bound traffic crosses the
boundary exclusively through Qt signals (thread-safe, auto-queued); GUI-to-app
traffic uses :func:`asyncio.run_coroutine_threadsafe`. Permission prompts are
marshalled to the GUI thread via a queued signal and resolved back into an
asyncio future.
"""

from __future__ import annotations

import asyncio
import contextlib
import threading
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QMessageBox

from jarvis.agents.base import AgentResult
from jarvis.core.logging import get_logger

if TYPE_CHECKING:
    from jarvis.app import JarvisApp
    from jarvis.core.events import Event

logger = get_logger("gui.bridge")

_SHUTDOWN_TIMEOUT = 6.0


class JarvisBridge(QObject):
    """Runs JarvisApp on a dedicated asyncio loop and mirrors it into Qt signals.

    Construct with a *factory* returning the ``JarvisApp.create(...)`` coroutine;
    the app is built inside the worker loop so every asyncio primitive it
    creates is bound to that loop.
    """

    delta = Signal(str)  # streaming answer text chunk
    answer = Signal(str)  # final answer text
    event = Signal(str, object)  # (topic, data) from the EventBus
    level = Signal(float)  # voice loudness 0..1
    started = Signal(object)  # JarvisApp.status() dict once online
    error = Signal(str)  # human-readable failure notice

    _confirm_requested = Signal(str, str, object)  # capability, description, future

    def __init__(
        self,
        app_factory: Callable[[], Coroutine[Any, Any, JarvisApp]],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._factory = app_factory
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._app: JarvisApp | None = None
        self._loop_ready = threading.Event()
        # Queued connection: the dialog must run on the GUI thread that owns us.
        self._confirm_requested.connect(
            self._show_confirm_dialog, Qt.ConnectionType.QueuedConnection
        )

    # -- lifecycle --------------------------------------------------------------

    def start(self) -> None:
        """Start the worker thread and begin building the app inside it."""
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run_loop, name="jarvis-loop", daemon=True)
        self._thread.start()
        self._loop_ready.wait(timeout=5.0)

    def _run_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        loop.call_soon(lambda: loop.create_task(self._bootstrap()))
        self._loop_ready.set()
        try:
            loop.run_forever()
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

    async def _bootstrap(self) -> None:
        try:
            self._app = await self._factory()
        except Exception as exc:
            logger.exception("JarvisApp failed to start")
            self.error.emit(f"Startup failed: {exc}")
            return
        self._app.events.subscribe("*", self._on_bus_event)
        self._app.permissions.set_confirmer(self._confirm)
        self._app.start_hot_reload()
        self.started.emit(self._app.status())

    def shutdown(self) -> None:
        """Close the app and stop the worker loop; safe to call more than once."""
        loop = self._loop
        if loop is None or not loop.is_running():
            return
        if self._app is not None:
            future = asyncio.run_coroutine_threadsafe(self._app.aclose(), loop)
            with contextlib.suppress(Exception):
                future.result(timeout=_SHUTDOWN_TIMEOUT)
            self._app = None
        loop.call_soon_threadsafe(loop.stop)
        if self._thread is not None:
            self._thread.join(timeout=_SHUTDOWN_TIMEOUT)
            self._thread = None

    # -- app -> GUI ---------------------------------------------------------------

    def _on_bus_event(self, event: Event) -> None:
        """EventBus handler (worker thread): mirror events into Qt signals."""
        data = dict(event.data)
        if event.topic == "voice.level":
            with contextlib.suppress(TypeError, ValueError):
                self.level.emit(float(data.get("level", 0.0)))
        self.event.emit(event.topic, data)

    # -- GUI -> app ---------------------------------------------------------------

    def send_text(self, text: str) -> None:
        """Ask JARVIS; deltas/answer arrive via the :attr:`delta`/:attr:`answer` signals."""
        loop = self._loop
        if loop is None or not loop.is_running() or self._app is None:
            self.error.emit("JARVIS is still starting up - try again in a moment.")
            return
        asyncio.run_coroutine_threadsafe(self._ask(text), loop)

    async def _ask(self, text: str) -> None:
        assert self._app is not None
        try:
            async for item in self._app.ask_stream(text):
                if isinstance(item, AgentResult):
                    self.answer.emit(item.output)
                else:
                    self.delta.emit(str(item))
        except Exception as exc:
            logger.exception("ask_stream failed")
            self.error.emit(f"Request failed: {exc}")

    # -- permission confirmations ---------------------------------------------------

    async def _confirm(self, capability: str, description: str) -> bool:
        """Async confirmer for PermissionManager: dialog on the GUI thread."""
        loop = asyncio.get_running_loop()
        future: asyncio.Future[bool] = loop.create_future()
        self._confirm_requested.emit(capability, description, future)
        return await future

    @Slot(str, str, object)
    def _show_confirm_dialog(self, capability: str, description: str, future: object) -> None:
        box = QMessageBox()
        box.setWindowTitle("JARVIS - Permission")
        box.setIcon(QMessageBox.Icon.Question)
        box.setText(f"Allow capability '{capability}'?")
        box.setInformativeText(description)
        box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        box.setDefaultButton(QMessageBox.StandardButton.No)
        approved = box.exec() == QMessageBox.StandardButton.Yes
        self._resolve_future(future, approved)

    def _resolve_future(self, future: object, result: bool) -> None:
        loop = self._loop
        if loop is None or not loop.is_running() or not isinstance(future, asyncio.Future):
            return

        def _set() -> None:
            if not future.done():
                future.set_result(result)

        loop.call_soon_threadsafe(_set)
