"""JARVIS HUD (PySide6).

PySide6 is an optional extra (``pip install jarvis-assistant[gui]``), so this
package must import cleanly without it. Everything Qt-flavoured is therefore
loaded lazily via module ``__getattr__``; only :mod:`jarvis.gui.logic` (pure
Python) is safe to import unconditionally.
"""

from __future__ import annotations

from typing import Any

__all__ = ["run_gui"]


def __getattr__(name: str) -> Any:
    """Lazily resolve :func:`run_gui` so importing the package never needs Qt."""
    if name == "run_gui":
        try:
            from jarvis.gui.main import run_gui
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise ImportError(
                "The JARVIS GUI requires PySide6. "
                "Install it with: pip install 'jarvis-assistant[gui]'"
            ) from exc
        return run_gui
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
