"""Zentrales Logging für Jarvis: Konsole + Logdatei."""

import logging
from pathlib import Path

from jarvis.utils.config_loader import PROJECT_ROOT


def setup_logger(name: str, config: dict) -> logging.Logger:
    """Erstellt einen Logger, der in Konsole und Datei schreibt."""
    log_cfg = config.get("logging", {})
    level = getattr(logging, log_cfg.get("level", "INFO").upper(), logging.INFO)

    log_file = PROJECT_ROOT / log_cfg.get("file", "logs/jarvis.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Doppelte Handler vermeiden, falls setup_logger mehrfach aufgerufen wird
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
