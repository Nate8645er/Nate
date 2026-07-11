"""Windows-only window management helpers.

All functions raise :class:`DesktopError` on non-Windows platforms; the heavy
dependencies (pygetwindow, ctypes user32 calls) are imported lazily so this
module is importable everywhere.
"""

from __future__ import annotations

import sys
from typing import Any

from jarvis.core.errors import DesktopError

_NOT_WINDOWS = "Window management is only available on Windows"


def _ensure_windows() -> None:
    if sys.platform != "win32":
        raise DesktopError(_NOT_WINDOWS)


def _pygetwindow() -> Any:
    _ensure_windows()
    try:
        import pygetwindow
    except ImportError as exc:
        raise DesktopError(
            "pygetwindow is not installed. Install it with: "
            "pip install 'jarvis-assistant[desktop]'",
            cause=exc,
        ) from exc
    return pygetwindow


def _find_window(title: str) -> Any:
    """Return the first window whose title contains *title*."""
    gw = _pygetwindow()
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        raise DesktopError(f"No window matching '{title}' found")
    return windows[0]


def focus_window(title: str) -> str:
    """Bring the first window matching *title* to the foreground."""
    window = _find_window(title)
    try:
        if window.isMinimized:
            window.restore()
        window.activate()
    except Exception as exc:  # pygetwindow raises plain Exception subclasses
        raise DesktopError(f"Could not focus window '{title}': {exc}", cause=exc) from exc
    return f"Focused window '{window.title}'"


def minimize_window(title: str) -> str:
    """Minimize the first window matching *title*."""
    window = _find_window(title)
    try:
        window.minimize()
    except Exception as exc:
        raise DesktopError(f"Could not minimize window '{title}': {exc}", cause=exc) from exc
    return f"Minimized window '{window.title}'"


def maximize_window(title: str) -> str:
    """Maximize the first window matching *title*."""
    window = _find_window(title)
    try:
        window.maximize()
    except Exception as exc:
        raise DesktopError(f"Could not maximize window '{title}': {exc}", cause=exc) from exc
    return f"Maximized window '{window.title}'"


def get_active_window_title() -> str:
    """Return the title of the currently focused window."""
    _ensure_windows()
    try:
        import pygetwindow

        window = pygetwindow.getActiveWindow()
        if window is not None:
            return window.title
    except ImportError:
        pass  # fall back to raw WinAPI below
    import ctypes

    user32 = ctypes.windll.user32
    handle = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(handle)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(handle, buffer, length + 1)
    return buffer.value
