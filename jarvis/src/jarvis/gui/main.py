"""GUI entry point: builds the Qt application, the bridge and the HUD window."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from jarvis.app import JarvisApp
from jarvis.core.config import JarvisConfig
from jarvis.gui.bridge import JarvisBridge
from jarvis.gui.main_window import JarvisMainWindow


def run_gui(config: JarvisConfig | None = None) -> None:
    """Launch the JARVIS HUD and block until the window closes.

    The JarvisApp itself is created lazily *inside* the bridge's worker event
    loop, so all of its asyncio primitives belong to that loop. The bridge is
    always shut down on exit, even if the Qt loop raises.
    """
    if config is None:
        from jarvis.core.config import load_config

        config = load_config()

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(config.assistant_name)
    app.setQuitOnLastWindowClosed(True)

    bridge = JarvisBridge(lambda: JarvisApp.create(config))
    window = JarvisMainWindow(config, bridge)
    bridge.start()
    window.show()
    try:
        app.exec()
    finally:
        bridge.shutdown()


if __name__ == "__main__":
    from jarvis.core.config import load_config

    run_gui(load_config())
