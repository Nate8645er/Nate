"""Mouse and keyboard control through pyautogui (imported lazily).

pyautogui needs a real display; on headless machines the import itself fails.
Every entry point therefore goes through :meth:`InputController._gui`, which
raises a :class:`DesktopError` with an install hint instead of crashing.
"""

from __future__ import annotations

from typing import Any, Literal

from jarvis.core.config import DesktopConfig
from jarvis.core.errors import DesktopError

MouseButton = Literal["left", "middle", "right"]

_INSTALL_HINT = (
    "pyautogui is not available (it needs a graphical desktop session). "
    "Install it with: pip install 'jarvis-assistant[desktop]'"
)


class InputController:
    """Thin, config-aware wrapper around pyautogui."""

    def __init__(self, config: DesktopConfig) -> None:
        self._config = config
        self._pyautogui: Any = None

    def _gui(self) -> Any:
        """Import and configure pyautogui on first use."""
        if self._pyautogui is None:
            try:
                import pyautogui
            except Exception as exc:  # ImportError, or display errors on headless hosts
                raise DesktopError(_INSTALL_HINT, cause=exc) from exc
            pyautogui.FAILSAFE = self._config.failsafe
            pyautogui.PAUSE = self._config.action_pause_seconds
            self._pyautogui = pyautogui
        return self._pyautogui

    def screen_size(self) -> dict[str, int]:
        """Return the primary screen size in pixels."""
        size = self._gui().size()
        return {"width": int(size[0]), "height": int(size[1])}

    def move_mouse(self, x: int, y: int, duration: float = 0.0) -> str:
        """Move the mouse cursor to absolute coordinates."""
        self._gui().moveTo(x, y, duration=duration)
        return f"Mouse moved to ({x}, {y})"

    def click(
        self,
        x: int | None = None,
        y: int | None = None,
        button: MouseButton = "left",
        double: bool = False,
    ) -> str:
        """Click at the given coordinates (or the current position)."""
        if button not in ("left", "middle", "right"):
            raise DesktopError(f"Unknown mouse button '{button}'")
        self._gui().click(x=x, y=y, button=button, clicks=2 if double else 1)
        where = f"({x}, {y})" if x is not None and y is not None else "current position"
        return f"{'Double-clicked' if double else 'Clicked'} {button} at {where}"

    def scroll(self, amount: int, x: int | None = None, y: int | None = None) -> str:
        """Scroll vertically; positive *amount* scrolls up, negative down."""
        self._gui().scroll(amount, x=x, y=y)
        return f"Scrolled {amount}"

    def type_text(self, text: str, interval: float = 0.0) -> str:
        """Type *text* on the keyboard with an optional per-key delay."""
        self._gui().typewrite(text, interval=interval)
        return f"Typed {len(text)} characters"

    def hotkey(self, *keys: str) -> str:
        """Press a key combination, e.g. ``hotkey('ctrl', 'c')``."""
        if not keys:
            raise DesktopError("hotkey needs at least one key")
        self._gui().hotkey(*keys)
        return f"Pressed {'+'.join(keys)}"

    def key_press(self, key: str) -> str:
        """Press and release a single key."""
        if not key:
            raise DesktopError("key_press needs a key name")
        self._gui().press(key)
        return f"Pressed {key}"
