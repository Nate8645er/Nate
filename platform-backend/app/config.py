"""Config-Layer — eine Quelle der Wahrheit, mit ehrlichem 'not-configured'.

Übernimmt das Muster des bestehenden Systems (lib/supabase.ts, lib/ratelimit.ts):
Jede externe Anbindung meldet ehrlich, wenn Key/URL fehlt — kein Schein-Betrieb.
Werte kommen ausschließlich aus der Umgebung (12-Factor); nichts wird geraten.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    v = value.strip()
    return v or None


@dataclass(frozen=True)
class ServiceConfig:
    """Konfiguration eines externen Dienstes + ob er nutzbar ist."""

    name: str
    url: str | None
    #: Weitere Pflichtfelder (z. B. Token). None-Einträge = fehlend.
    secrets: tuple[str | None, ...] = ()

    @property
    def configured(self) -> bool:
        """True nur, wenn URL und alle Secrets gesetzt sind (honest)."""
        if not self.url:
            return False
        return all(s for s in self.secrets)

    def require(self) -> None:
        if not self.configured:
            raise RuntimeError(f"{self.name}: nicht-konfiguriert")


class Settings:
    """Liest die Umgebung EINMAL und stellt getippte Dienste bereit.

    Bewusst ohne pydantic-Zwang im Kern, damit der Config-Layer auch ohne
    installierte Abhängigkeiten importierbar/testbar bleibt.
    """

    def __init__(self, env: dict[str, str] | None = None) -> None:
        e = env if env is not None else dict(os.environ)
        self._env = e
        self.env_name = _clean(e.get("PLATFORM_ENV")) or "development"

        self.postgres = ServiceConfig(
            "postgres", _clean(e.get("DATABASE_URL")),
        )
        self.redis = ServiceConfig(
            "redis", _clean(e.get("REDIS_URL")),
        )
        self.qdrant = ServiceConfig(
            "qdrant", _clean(e.get("QDRANT_URL")),
            secrets=(),  # API-Key optional (lokal ohne)
        )
        self.temporal = ServiceConfig(
            "temporal", _clean(e.get("TEMPORAL_ADDRESS")),
        )
        self.minio = ServiceConfig(
            "minio", _clean(e.get("MINIO_ENDPOINT")),
            secrets=(_clean(e.get("MINIO_ACCESS_KEY")), _clean(e.get("MINIO_SECRET_KEY"))),
        )
        # Lokale Inferenz (Ollama/vLLM/LM-Studio) — OpenAI-kompatibel.
        self.local_llm = ServiceConfig(
            "local_llm", _clean(e.get("LOCAL_LLM_URL")),
            secrets=(),  # keyOptional (selbst gehostet)
        )
        # Auth (Keycloak/OIDC, §3). Issuer = Realm-URL; Audience (client_id)
        # optional, aber in Produktion empfohlen (siehe SECURITY-REVIEW.md).
        self.keycloak_issuer = _clean(e.get("KEYCLOAK_ISSUER"))
        self.keycloak_audience = _clean(e.get("KEYCLOAK_AUDIENCE"))

    @property
    def auth_configured(self) -> bool:
        """True nur, wenn ein OIDC-Issuer gesetzt ist (honest not-configured)."""
        return bool(self.keycloak_issuer)

    def get(self, key: str) -> str | None:
        return _clean(self._env.get(key))

    def snapshot(self) -> dict[str, bool]:
        """Für /health: welcher Dienst ist konfiguriert (ohne Secrets zu zeigen)."""
        return {
            "postgres": self.postgres.configured,
            "redis": self.redis.configured,
            "qdrant": self.qdrant.configured,
            "temporal": self.temporal.configured,
            "minio": self.minio.configured,
            "local_llm": self.local_llm.configured,
            "auth": self.auth_configured,
        }


#: Prozessweite Instanz (lazily via get_settings, damit Tests eigene Envs setzen können).
_settings: Settings | None = None


def get_settings(env: dict[str, str] | None = None) -> Settings:
    global _settings
    if env is not None:
        return Settings(env)
    if _settings is None:
        _settings = Settings()
    return _settings
