"""Application launching and process management (psutil is imported lazily)."""

from __future__ import annotations

import contextlib
import shlex
import shutil
import subprocess
import sys
from typing import Any

from jarvis.core.errors import DesktopError


def _psutil() -> Any:
    """Import psutil lazily so the module loads without the optional dependency."""
    try:
        import psutil
    except ImportError as exc:
        raise DesktopError(
            "psutil is not installed. Install it with: pip install 'jarvis-assistant[desktop]'",
            cause=exc,
        ) from exc
    return psutil


def launch_app(command_or_name: str) -> dict[str, Any]:
    """Launch an application as a detached process.

    Accepts a bare executable name or a full command line; the executable must
    be resolvable via ``PATH``. Returns the new process id and executable path.
    """
    parts = shlex.split(command_or_name, posix=(sys.platform != "win32"))
    if not parts:
        raise DesktopError("Cannot launch: empty command")
    executable = shutil.which(parts[0])
    if executable is None:
        raise DesktopError(f"Executable '{parts[0]}' was not found on PATH")
    popen_kwargs: dict[str, Any] = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        popen_kwargs["start_new_session"] = True
    try:
        process = subprocess.Popen([executable, *parts[1:]], **popen_kwargs)
    except OSError as exc:
        raise DesktopError(f"Failed to launch '{command_or_name}': {exc}", cause=exc) from exc
    return {"pid": process.pid, "executable": executable}


def close_app(name_or_pid: str | int, timeout: float = 5.0) -> str:
    """Terminate processes by PID or (substring) name.

    Sends ``terminate`` first and escalates to ``kill`` for processes still
    alive after *timeout* seconds.
    """
    ps = _psutil()
    token = str(name_or_pid).strip()
    if not token:
        raise DesktopError("Cannot close: empty process name or PID")
    if token.isdigit():
        try:
            targets = [ps.Process(int(token))]
        except ps.NoSuchProcess as exc:
            raise DesktopError(f"No process with PID {token}", cause=exc) from exc
    else:
        needle = token.lower()
        targets = [
            proc
            for proc in ps.process_iter(["name"])
            if needle in (proc.info.get("name") or "").lower()
        ]
        if not targets:
            raise DesktopError(f"No running process matches '{token}'")
    for proc in targets:
        with contextlib.suppress(ps.NoSuchProcess, ps.AccessDenied):
            proc.terminate()
    _, alive = ps.wait_procs(targets, timeout=timeout)
    for proc in alive:
        with contextlib.suppress(ps.NoSuchProcess, ps.AccessDenied):
            proc.kill()
    return f"Terminated {len(targets)} process(es) matching '{token}'"


def list_processes(name_filter: str = "", limit: int = 50) -> list[dict[str, Any]]:
    """List running processes (pid, name, resident memory), largest first."""
    ps = _psutil()
    needle = name_filter.lower()
    results: list[dict[str, Any]] = []
    for proc in ps.process_iter(["pid", "name", "memory_info"]):
        info = proc.info
        name = info.get("name") or ""
        if needle and needle not in name.lower():
            continue
        memory = info.get("memory_info")
        results.append(
            {
                "pid": int(info["pid"]),
                "name": name,
                "memory_mb": round(memory.rss / 1_048_576, 1) if memory else 0.0,
            }
        )
    results.sort(key=lambda item: item["memory_mb"], reverse=True)
    return results[: max(1, limit)]
