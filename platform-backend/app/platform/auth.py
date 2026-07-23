"""Keycloak / OIDC-Token-Verifikation (Auftrag §3: Auth = Keycloak).

Primäre Auth-Implementierung des NEUEN Backends. Verifiziert von Keycloak
ausgestellte RS256-JWTs gegen den JWKS-Endpunkt des Realms und prüft
Aussteller, Ablauf und (optional) Audience.

Wichtig: Die bestehende Vercel-App nutzt weiterhin Supabase-Auth. Diese Schicht
ersetzt sie NICHT im laufenden Produkt — sie ist der §3-konforme Pfad des neuen
Backends, auf den später per Feature-Flag umgeschaltet wird.

Der JWKS-Bezug ist injizierbar → Verifikation ist ohne laufenden Keycloak
testbar (Test speist einen selbst signierten Schlüssel als JWKS ein).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import jwt
from jwt import PyJWK, PyJWKSet

#: Liefert das JWKS (dict) für einen Realm. Default: HTTP gegen Keycloak.
JwksProvider = Callable[[], dict]


@dataclass(frozen=True)
class OidcConfig:
    issuer: str                 # z. B. https://auth.example.com/realms/kunden
    audience: str | None = None  # optional erzwungene Audience (client_id)

    @property
    def jwks_url(self) -> str:
        return self.issuer.rstrip("/") + "/protocol/openid-connect/certs"


@dataclass(frozen=True)
class Principal:
    """Verifizierter Aufrufer. `tenant` = Realm/Gruppe für Mandantentrennung."""

    subject: str
    tenant: str | None
    roles: frozenset[str]
    email: str | None


class TokenError(Exception):
    """Token ungültig/abgelaufen/falscher Aussteller. Nie leise durchlassen."""


class KeycloakVerifier:
    def __init__(self, config: OidcConfig, jwks_provider: JwksProvider) -> None:
        self._cfg = config
        self._jwks_provider = jwks_provider

    def _signing_key(self, token: str) -> PyJWK:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        jwks = PyJWKSet.from_dict(self._jwks_provider())
        for key in jwks.keys:
            if key.key_id == kid:
                return key
        raise TokenError(f"kein passender Schlüssel (kid={kid})")

    def verify(self, token: str) -> Principal:
        try:
            key = self._signing_key(token)
            options = {"require": ["exp", "iat"], "verify_aud": self._cfg.audience is not None}
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                audience=self._cfg.audience,
                issuer=self._cfg.issuer,
                options=options,
            )
        except TokenError:
            raise
        except jwt.PyJWTError as exc:  # abgelaufen, falscher iss/aud, Signatur …
            raise TokenError(str(exc)) from exc

        realm_roles = claims.get("realm_access", {}).get("roles", [])
        return Principal(
            subject=str(claims.get("sub", "")),
            # Mandant: bevorzugt expliziter Claim, sonst Realm aus dem Issuer.
            tenant=claims.get("tenant") or _realm_from_issuer(self._cfg.issuer),
            roles=frozenset(realm_roles),
            email=claims.get("email"),
        )


def _realm_from_issuer(issuer: str) -> str | None:
    # …/realms/<name>
    parts = issuer.rstrip("/").split("/realms/")
    return parts[1] if len(parts) == 2 and parts[1] else None
