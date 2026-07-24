"""Zentrale Konfiguration. Alle Werte kommen aus der Umgebung (.env),
niemals aus dem Code (Master-Prompt Regel 4: keine Secrets im Repo)."""
from __future__ import annotations

import os


def _req(name: str, default: str | None = None) -> str:
    val = os.environ.get(name, default)
    if val is None:
        raise RuntimeError(f"Pflicht-Umgebungsvariable {name} fehlt")
    return val


class Settings:
    # Laufzeit-Verbindung: MUSS eine RLS-gebundene Rolle sein
    # (NOSUPERUSER, NOBYPASSRLS, nicht Tabellen-Owner). Sonst wird RLS
    # umgangen und die Mandantentrennung ist wirkungslos. Kein Default —
    # fehlt die Variable, soll der Start fehlschlagen (fail-closed).
    database_url: str = _req("DATABASE_URL")

    # Migrations-Verbindung: privilegierte Rolle (Owner/Superuser), die DDL
    # ausfuehren darf. Faellt auf database_url zurueck (Single-Role-Betrieb),
    # sollte in Produktion aber getrennt sein.
    migrate_database_url: str = os.environ.get(
        "MIGRATE_DATABASE_URL"
    ) or _req("DATABASE_URL")

    # LiteLLM-Gateway (OpenAI-kompatibel). Ein Gateway fuer alle Anbieter.
    litellm_base_url: str = os.environ.get("LITELLM_BASE_URL", "http://localhost:4000")
    litellm_master_key: str = os.environ.get("LITELLM_MASTER_KEY", "")

    # Betrieb
    request_timeout_s: float = float(os.environ.get("REQUEST_TIMEOUT_S", "120"))
    # Kommagetrennte Liste erlaubter CORS-Origins; leer = nur same-origin.
    cors_origins: list[str] = [
        o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
    ]


settings = Settings()
