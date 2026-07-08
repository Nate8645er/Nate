"""Zentrale Stelle für geheime Schlüssel (API-Keys).

Die Schlüssel werden NIE im Code oder in config.json gespeichert.
Gesucht wird in dieser Reihenfolge:
  1. Umgebungsvariable (z.B. ANTHROPIC_API_KEY)
  2. config/secrets.json  (steht in .gitignore, landet nie auf GitHub)
"""

import json
import logging
import os

from jarvis.utils.config_loader import PROJECT_ROOT

logger = logging.getLogger("jarvis.secrets")

SECRETS_PATH = PROJECT_ROOT / "config" / "secrets.json"


def load_secret(name: str, env_var: str | None = None) -> str | None:
    """Holt einen Schlüssel aus der Umgebung oder aus config/secrets.json."""
    if env_var:
        value = os.environ.get(env_var)
        if value:
            return value
    if SECRETS_PATH.exists():
        try:
            secrets = json.loads(SECRETS_PATH.read_text(encoding="utf-8"))
            return secrets.get(name) or None
        except (OSError, json.JSONDecodeError) as e:
            logger.error("secrets.json konnte nicht gelesen werden: %s", e)
    return None
