"""Cross-platform window enumeration (best effort).

Strategy, in order of fidelity:

1. ``pygetwindow`` on Windows (real window handles).
2. ``wmctrl -l`` on Linux (X11 window IDs; requires the ``wmctrl`` binary).
3. ``psutil`` process list everywhere as a last resort — entries are
   processes, not windows, and are labelled ``source="processes"``.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any

from jarvis.core.errors import VisionError
from jarvis.core.logging import get_logger

logger = get_logger("vision.windows")

WindowInfo = dict[str, Any]  # {title: str, handle_or_pid: Any, source: str}


def list_windows() -> list[WindowInfo]:
    """Return open windows as ``{title, handle_or_pid, source}`` dicts.

    Falls back gracefully across backends; when only the process list is
    available the entries describe processes (``source="processes"``)
    rather than actual windows.
    """
    if sys.platform == "win32":
        windows = _pygetwindow_windows()
        if windows is not None:
            return windows
    elif sys.platform.startswith("linux"):
        windows = _wmctrl_windows()
        if windows is not None:
            return windows
    return _process_fallback()


def _pygetwindow_windows() -> list[WindowInfo] | None:
    """Enumerate windows via pygetwindow; ``None`` when unusable."""
    try:
        import pygetwindow
    except ImportError:
        logger.debug("pygetwindow not installed")
        return None
    try:
        windows: list[WindowInfo] = []
        for win in pygetwindow.getAllWindows():
            title = (win.title or "").strip()
            if not title:
                continue
            windows.append(
                {
                    "title": title,
                    "handle_or_pid": getattr(win, "_hWnd", None),
                    "source": "pygetwindow",
                }
            )
        return windows
    except Exception:
        logger.debug("pygetwindow enumeration failed", exc_info=True)
        return None


def _wmctrl_windows() -> list[WindowInfo] | None:
    """Enumerate windows via ``wmctrl -l``; ``None`` when unusable."""
    try:
        proc = subprocess.run(
            ["wmctrl", "-l"], capture_output=True, text=True, timeout=5, check=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logger.debug("wmctrl unavailable: %s", exc)
        return None
    windows: list[WindowInfo] = []
    for line in proc.stdout.splitlines():
        # Format: <window id> <desktop> <host> <title...>
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        windows.append({"title": parts[3], "handle_or_pid": parts[0], "source": "wmctrl"})
    return windows


def _process_fallback() -> list[WindowInfo]:
    """Return the running-process list (labelled ``source="processes"``)."""
    try:
        import psutil
    except ImportError as exc:
        raise VisionError(
            "No window-listing backend available. Install 'wmctrl' (Linux), "
            "'pygetwindow' (Windows), or at least 'psutil' for a process list "
            "(pip install psutil).",
            cause=exc,
        ) from exc
    entries: list[WindowInfo] = []
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        try:
            info = proc.info
            pid = int(info["pid"])
            entries.append(
                {
                    "title": info.get("name") or f"pid-{pid}",
                    "handle_or_pid": pid,
                    "source": "processes",
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return entries
