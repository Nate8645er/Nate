"""Asynchronous shell command execution with timeout and output truncation."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from jarvis.core.errors import DesktopError

_MAX_OUTPUT_CHARS = 20_000


async def run_command(
    command: str,
    cwd: str | None = None,
    timeout: float = 120.0,
    env: dict[str, str] | None = None,
) -> dict[str, str | int]:
    """Run a shell command and return ``{"stdout", "stderr", "exit_code"}``.

    The process environment is inherited (with *env* merged on top), both
    output streams are captured and truncated to 20k characters, and the
    process is killed once *timeout* seconds elapse (``exit_code`` -1).
    """
    if not command.strip():
        raise DesktopError("Cannot run: empty command")
    workdir: str | None = None
    if cwd:
        path = Path(cwd).expanduser()
        if not path.is_dir():
            raise DesktopError(f"Working directory does not exist: '{cwd}'")
        workdir = str(path)
    merged_env = {**os.environ, **(env or {})}
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=workdir,
            env=merged_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as exc:
        raise DesktopError(f"Failed to start command: {exc}", cause=exc) from exc
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except TimeoutError:
        process.kill()
        await process.wait()
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "exit_code": -1,
        }
    return {
        "stdout": stdout.decode("utf-8", "replace")[:_MAX_OUTPUT_CHARS],
        "stderr": stderr.decode("utf-8", "replace")[:_MAX_OUTPUT_CHARS],
        "exit_code": process.returncode if process.returncode is not None else -1,
    }
