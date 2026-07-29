"""API-Dependencies — die HTTP-Auth-Kette (Phase 9 · Cutover-Integration).

Verbindet die vorhandene, getestete Auth/RBAC-Logik (`platform/auth.py`,
`platform/rbac.py`) mit FastAPI. Ehrlich:
- Ist **kein** Keycloak-Issuer konfiguriert, liefern geschützte Endpunkte
  **503** („Auth nicht konfiguriert") — kein Schein-Login, kein Default-User.
- Fehlt/ungültig das Bearer-Token → **401**.
- Fehlt ein Recht → **403** (RBAC Default-Deny).

Der JWKS-Bezug ist über `set_verifier_override` injizierbar (Tests speisen einen
selbst signierten Schlüssel ein — kein laufender Keycloak nötig).
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status

from ..config import get_settings
from ..platform.auth import KeycloakVerifier, OidcConfig, Principal, TokenError
from ..platform.rbac import Permission, PermissionDenied, require

#: Test-/DI-Hook: gesetzt → dieser Verifier wird genutzt (statt echtem JWKS-HTTP).
_verifier_override: KeycloakVerifier | None = None


def set_verifier_override(verifier: KeycloakVerifier | None) -> None:
    global _verifier_override
    _verifier_override = verifier


def _build_verifier() -> KeycloakVerifier | None:
    """Baut den Verifier aus der Konfiguration; None, wenn Auth nicht gesetzt."""
    if _verifier_override is not None:
        return _verifier_override
    s = get_settings()
    if not s.auth_configured:
        return None
    import httpx

    cfg = OidcConfig(issuer=s.keycloak_issuer or "", audience=s.keycloak_audience)

    def jwks_provider() -> dict:
        resp = httpx.get(cfg.jwks_url, timeout=5.0)
        resp.raise_for_status()
        return resp.json()

    return KeycloakVerifier(cfg, jwks_provider)


def require_principal(authorization: str | None = Header(default=None)) -> Principal:
    """FastAPI-Dependency: verifizierter Aufrufer oder passender HTTP-Fehler."""
    verifier = _build_verifier()
    if verifier is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth nicht konfiguriert (KEYCLOAK_ISSUER fehlt)",
        )
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer-Token fehlt")
    token = authorization.split(" ", 1)[1].strip()
    try:
        return verifier.verify(token)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_permission(permission: Permission) -> Callable[[Principal], Principal]:
    """Baut eine Dependency, die zusätzlich ein RBAC-Recht erzwingt."""

    def _dep(principal: Principal = Depends(require_principal)) -> Principal:
        try:
            require(principal, permission)
        except PermissionDenied as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        return principal

    return _dep
