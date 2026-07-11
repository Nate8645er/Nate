"""Structured logging setup for JARVIS.

Uses the standard library so no extra dependency is required at runtime;
``rich`` is used for the console handler when available.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_CONFIGURED = False


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for machine ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            payload["exception"] = self.formatException(record.exc_info)
        extra = getattr(record, "context", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(
    level: str = "INFO",
    log_dir: Path | None = None,
    json_console: bool = False,
) -> None:
    """Configure root logging once. Subsequent calls are no-ops."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    root = logging.getLogger()
    root.setLevel(level.upper())

    console: logging.Handler
    if json_console:
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(JsonFormatter())
    else:
        try:
            from rich.logging import RichHandler

            console = RichHandler(rich_tracebacks=True, show_path=False)
            console.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
        except ImportError:
            console = logging.StreamHandler(sys.stderr)
            console.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
            )
    root.addHandler(console)

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / "jarvis.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(JsonFormatter())
        root.addHandler(file_handler)

    # Third-party noise reduction.
    for noisy in ("httpx", "httpcore", "urllib3", "watchfiles"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger (``jarvis.<name>`` unless already qualified)."""
    if not name.startswith("jarvis"):
        name = f"jarvis.{name}"
    return logging.getLogger(name)
