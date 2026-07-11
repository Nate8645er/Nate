"""Desktop automation subsystem: files, apps, input, office documents, terminal, windows.

:func:`register` wires every desktop tool into the application's tool
registry. Only the standard library and JARVIS core are imported at module
level; the heavy optional dependencies (pyautogui, psutil, pypdf, openpyxl,
python-docx, python-pptx, pygetwindow) are imported lazily by the individual
modules, so importing this package always succeeds and handlers return clear
error strings when a dependency is missing.
"""

from __future__ import annotations

import asyncio
import functools
from typing import TYPE_CHECKING, Any, Literal, cast

from jarvis.core.errors import DesktopError
from jarvis.desktop import apps, office, terminal, winapi
from jarvis.desktop.files import FileManager
from jarvis.desktop.input import InputController

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from jarvis.app import JarvisApp

__all__ = ["FileManager", "InputController", "register"]

_STR = {"type": "string"}
_INT = {"type": "integer"}
_NUM = {"type": "number"}
_BOOL = {"type": "boolean"}


def _params(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def _safe(handler: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Turn :class:`DesktopError` raised by *handler* into a readable string."""

    @functools.wraps(handler)
    async def wrapper(**kwargs: Any) -> Any:
        try:
            return await handler(**kwargs)
        except DesktopError as exc:
            return f"Error: {exc.message}"

    return wrapper


def register(app: JarvisApp) -> None:
    """Register all desktop tools and services on *app*."""
    config = app.config
    files = FileManager(config)
    controller = InputController(config.desktop)
    app.container.register_instance(FileManager, files)
    app.container.register_instance(InputController, controller)
    tools = app.tools

    # -- files -----------------------------------------------------------------

    async def files_read(path: str, max_chars: int = 20_000) -> str:
        return await files.read_text(path, max_chars=max_chars)

    tools.register_function(
        "files_read",
        "Read a text file from an allowed directory (truncated to max_chars).",
        _safe(files_read),
        parameters=_params({"path": _STR, "max_chars": _INT}, ["path"]),
        tags={"files"},
        source="desktop",
    )

    async def files_write(path: str, content: str, append: bool = False) -> str:
        if append:
            written = await files.append_text(path, content)
            return f"Appended {len(content)} characters to {written}"
        written = await files.write_text(path, content)
        return f"Wrote {len(content)} characters to {written}"

    tools.register_function(
        "files_write",
        "Write (or append) text content to a file inside an allowed directory.",
        _safe(files_write),
        parameters=_params(
            {
                "path": _STR,
                "content": _STR,
                "append": {"type": "boolean", "description": "Append instead of overwrite"},
            },
            ["path", "content"],
        ),
        tags={"files"},
        capability="files.write",
        source="desktop",
    )

    async def files_delete(path: str) -> str:
        trashed = await files.delete(path)
        return f"Moved to trash: {trashed}"

    tools.register_function(
        "files_delete",
        "Delete a file or directory (soft delete: it is moved to the JARVIS trash).",
        _safe(files_delete),
        parameters=_params({"path": _STR}, ["path"]),
        tags={"files"},
        capability="files.delete",
        source="desktop",
    )

    async def files_move(source: str, destination: str) -> str:
        moved = await files.move(source, destination)
        return f"Moved to {moved}"

    tools.register_function(
        "files_move",
        "Move or rename a file or directory inside the allowed directories.",
        _safe(files_move),
        parameters=_params({"source": _STR, "destination": _STR}, ["source", "destination"]),
        tags={"files"},
        capability="files.write",
        source="desktop",
    )

    async def files_list(path: str) -> Any:
        return await files.list_dir(path)

    tools.register_function(
        "files_list",
        "List a directory with entry type, size in bytes and modification time.",
        _safe(files_list),
        parameters=_params({"path": _STR}, ["path"]),
        tags={"files"},
        source="desktop",
    )

    async def files_search(
        directory: str,
        pattern: str = "**/*",
        content: str = "",
        max_results: int = 50,
    ) -> Any:
        return await files.search(
            directory, pattern=pattern, content=content or None, max_results=max_results
        )

    tools.register_function(
        "files_search",
        "Find files below a directory by glob pattern, optionally filtered by a "
        "plain-text content substring.",
        _safe(files_search),
        parameters=_params(
            {
                "directory": _STR,
                "pattern": {"type": "string", "description": "Glob pattern, e.g. **/*.py"},
                "content": {"type": "string", "description": "Substring the file must contain"},
                "max_results": _INT,
            },
            ["directory"],
        ),
        tags={"files"},
        source="desktop",
    )

    # -- office ----------------------------------------------------------------

    async def office_read_pdf(path: str, pages: str = "") -> str:
        return await office.read_pdf(files, path, pages=pages)

    tools.register_function(
        "office_read_pdf",
        "Extract text from a PDF file. pages is an optional 1-based spec like '1-3,7'.",
        _safe(office_read_pdf),
        parameters=_params({"path": _STR, "pages": _STR}, ["path"]),
        tags={"office", "files"},
        source="desktop",
    )

    async def office_read_excel(path: str, sheet: str = "") -> Any:
        return await office.read_excel(files, path, sheet=sheet)

    tools.register_function(
        "office_read_excel",
        "Read an Excel worksheet (the active one by default) as a list of rows.",
        _safe(office_read_excel),
        parameters=_params({"path": _STR, "sheet": _STR}, ["path"]),
        tags={"office", "files"},
        source="desktop",
    )

    async def office_write_excel(
        path: str, rows: list[list[Any]], sheet: str = "Sheet1"
    ) -> str:
        written = await office.write_excel(files, path, rows, sheet=sheet)
        return f"Wrote {len(rows)} rows to {written}"

    tools.register_function(
        "office_write_excel",
        "Create an Excel .xlsx file from rows given as a list of lists.",
        _safe(office_write_excel),
        parameters=_params(
            {
                "path": _STR,
                "rows": {"type": "array", "items": {"type": "array"}},
                "sheet": _STR,
            },
            ["path", "rows"],
        ),
        tags={"office", "files"},
        capability="files.write",
        source="desktop",
    )

    async def office_read_word(path: str) -> str:
        return await office.read_word(files, path)

    tools.register_function(
        "office_read_word",
        "Read the paragraph text of a Word .docx document.",
        _safe(office_read_word),
        parameters=_params({"path": _STR}, ["path"]),
        tags={"office", "files"},
        source="desktop",
    )

    async def office_write_word(path: str, text: str) -> str:
        written = await office.write_word(files, path, text)
        return f"Created Word document {written}"

    tools.register_function(
        "office_write_word",
        "Create a Word .docx document from plain text. Lines starting with '#' "
        "become headings, other lines become paragraphs.",
        _safe(office_write_word),
        parameters=_params({"path": _STR, "text": _STR}, ["path", "text"]),
        tags={"office", "files"},
        capability="files.write",
        source="desktop",
    )

    async def office_read_powerpoint(path: str) -> str:
        return await office.read_powerpoint(files, path)

    tools.register_function(
        "office_read_powerpoint",
        "Extract all text from a PowerPoint .pptx presentation, slide by slide.",
        _safe(office_read_powerpoint),
        parameters=_params({"path": _STR}, ["path"]),
        tags={"office", "files"},
        source="desktop",
    )

    async def office_write_powerpoint(path: str, slides: list[dict[str, Any]]) -> str:
        written = await office.write_powerpoint(files, path, slides)
        return f"Created presentation with {len(slides)} slide(s): {written}"

    tools.register_function(
        "office_write_powerpoint",
        "Create a PowerPoint .pptx from slides given as "
        '[{"title": "...", "bullets": ["...", ...]}].',
        _safe(office_write_powerpoint),
        parameters=_params(
            {
                "path": _STR,
                "slides": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": _STR,
                            "bullets": {"type": "array", "items": _STR},
                        },
                    },
                },
            },
            ["path", "slides"],
        ),
        tags={"office", "files"},
        capability="files.write",
        source="desktop",
    )

    # -- applications & processes ------------------------------------------------

    async def app_launch(command: str) -> Any:
        return await asyncio.to_thread(apps.launch_app, command)

    tools.register_function(
        "app_launch",
        "Launch an application as a detached process (name or full command line).",
        _safe(app_launch),
        parameters=_params({"command": _STR}, ["command"]),
        tags={"desktop"},
        capability="desktop.apps",
        source="desktop",
    )

    async def app_close(target: str, timeout: float = 5.0) -> str:
        return await asyncio.to_thread(apps.close_app, target, timeout)

    tools.register_function(
        "app_close",
        "Close an application by name or PID (graceful terminate, then kill).",
        _safe(app_close),
        parameters=_params({"target": _STR, "timeout": _NUM}, ["target"]),
        tags={"desktop"},
        capability="desktop.apps",
        source="desktop",
    )

    async def processes_list(name_filter: str = "", limit: int = 50) -> Any:
        return await asyncio.to_thread(apps.list_processes, name_filter, limit)

    tools.register_function(
        "processes_list",
        "List running processes (pid, name, memory), optionally filtered by name.",
        _safe(processes_list),
        parameters=_params({"name_filter": _STR, "limit": _INT}),
        tags={"desktop"},
        source="desktop",
    )

    # -- mouse & keyboard ---------------------------------------------------------

    async def mouse_move(x: int, y: int, duration: float = 0.0) -> str:
        return await asyncio.to_thread(controller.move_mouse, x, y, duration)

    tools.register_function(
        "mouse_move",
        "Move the mouse cursor to absolute screen coordinates.",
        _safe(mouse_move),
        parameters=_params({"x": _INT, "y": _INT, "duration": _NUM}, ["x", "y"]),
        tags={"desktop"},
        capability="desktop.input",
        source="desktop",
    )

    async def mouse_click(
        x: int | None = None,
        y: int | None = None,
        button: str = "left",
        double: bool = False,
    ) -> str:
        if button not in ("left", "middle", "right"):
            return f"Error: unknown mouse button '{button}'"
        chosen = cast(Literal["left", "middle", "right"], button)
        return await asyncio.to_thread(controller.click, x, y, chosen, double)

    tools.register_function(
        "mouse_click",
        "Click the mouse at the given coordinates (or the current position).",
        _safe(mouse_click),
        parameters=_params(
            {
                "x": _INT,
                "y": _INT,
                "button": {"type": "string", "enum": ["left", "middle", "right"]},
                "double": _BOOL,
            }
        ),
        tags={"desktop"},
        capability="desktop.input",
        source="desktop",
    )

    async def keyboard_type(text: str, interval: float = 0.0) -> str:
        return await asyncio.to_thread(controller.type_text, text, interval)

    tools.register_function(
        "keyboard_type",
        "Type text on the keyboard into the focused window.",
        _safe(keyboard_type),
        parameters=_params({"text": _STR, "interval": _NUM}, ["text"]),
        tags={"desktop"},
        capability="desktop.input",
        source="desktop",
    )

    async def keyboard_hotkey(keys: list[str]) -> str:
        return await asyncio.to_thread(controller.hotkey, *keys)

    tools.register_function(
        "keyboard_hotkey",
        "Press a key combination, e.g. [\"ctrl\", \"c\"] or [\"alt\", \"tab\"].",
        _safe(keyboard_hotkey),
        parameters=_params({"keys": {"type": "array", "items": _STR}}, ["keys"]),
        tags={"desktop"},
        capability="desktop.input",
        source="desktop",
    )

    # -- terminal --------------------------------------------------------------

    async def terminal_run(command: str, cwd: str = "", timeout: float = 0.0) -> Any:
        effective_timeout = timeout if timeout > 0 else config.desktop.terminal_timeout_seconds
        return await terminal.run_command(command, cwd=cwd or None, timeout=effective_timeout)

    tools.register_function(
        "terminal_run",
        "Run a shell command and return stdout, stderr and exit_code.",
        _safe(terminal_run),
        parameters=_params(
            {
                "command": _STR,
                "cwd": {"type": "string", "description": "Working directory (optional)"},
                "timeout": {"type": "number", "description": "Seconds; 0 = configured default"},
            },
            ["command"],
        ),
        tags={"terminal"},
        capability="desktop.terminal",
        source="desktop",
    )

    # -- windows (Windows only) ---------------------------------------------------

    async def window_focus(title: str) -> str:
        return await asyncio.to_thread(winapi.focus_window, title)

    tools.register_function(
        "window_focus",
        "Focus the first window whose title contains the given text (Windows only).",
        _safe(window_focus),
        parameters=_params({"title": _STR}, ["title"]),
        tags={"desktop"},
        capability="desktop.input",
        source="desktop",
    )

    async def window_active() -> str:
        return await asyncio.to_thread(winapi.get_active_window_title)

    tools.register_function(
        "window_active",
        "Get the title of the currently focused window (Windows only).",
        _safe(window_active),
        tags={"desktop"},
        capability="desktop.input",
        source="desktop",
    )
