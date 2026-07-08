"""Lädt die zentrale Konfigurationsdatei config/config.json."""

import json
from pathlib import Path

# Projektwurzel = zwei Ebenen über dieser Datei (jarvis/utils/ -> Projektroot)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.json"


def load_config() -> dict:
    """Liest die Konfiguration ein und gibt sie als Dictionary zurück.

    Raises:
        FileNotFoundError: Wenn config/config.json fehlt.
        ValueError: Wenn die Datei kein gültiges JSON enthält.
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Konfigurationsdatei nicht gefunden: {CONFIG_PATH}"
        )
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Ungültiges JSON in {CONFIG_PATH}: {e}") from e
