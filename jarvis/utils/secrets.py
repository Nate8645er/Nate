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
EXAMPLE_PATH = PROJECT_ROOT / "config" / "secrets.example.json"

#: Noch nicht ausgefüllte Platzhalter aus der Vorlage erkennt man daran
PLACEHOLDER_MARKER = "HIER-DEINEN"


def load_secret(name: str, env_var: str | None = None) -> str | None:
    """Holt einen Schlüssel aus der Umgebung oder aus config/secrets.json.

    Platzhalter aus der Vorlage ("HIER-DEINEN-...") gelten als leer, damit
    eine halb ausgefüllte Datei keine kryptischen API-Fehler auslöst.
    """
    if env_var:
        value = os.environ.get(env_var)
        if value:
            return value
    if SECRETS_PATH.exists():
        try:
            secrets = json.loads(SECRETS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.error("secrets.json konnte nicht gelesen werden: %s", e)
            return None
        value = secrets.get(name) or None
        if value and PLACEHOLDER_MARKER in value:
            return None  # Platzhalter wurde noch nicht ersetzt
        return value
    return None


def ensure_secrets_file() -> bool:
    """Legt config/secrets.json mit Platzhaltern an, falls sie fehlt.

    Gibt True zurück, wenn die Datei gerade neu angelegt wurde - dann kann
    der Aufrufer den Nutzer darauf hinweisen, wo die Schlüssel hingehören.
    """
    if SECRETS_PATH.exists():
        return False
    try:
        if EXAMPLE_PATH.exists():
            SECRETS_PATH.write_text(
                EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8"
            )
        else:
            SECRETS_PATH.write_text("{}\n", encoding="utf-8")
        logger.info("config/secrets.json angelegt (mit Platzhaltern).")
        return True
    except OSError as e:
        logger.warning("secrets.json konnte nicht angelegt werden: %s", e)
        return False
