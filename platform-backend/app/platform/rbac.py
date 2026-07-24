"""RBAC — Rollen und Rechte (Auftrag §6).

Baut auf dem `Principal` aus `auth.py` (Keycloak-Rollen). Rechte werden zentral
Rollen zugeordnet; `require` erzwingt sie und wirft `PermissionDenied`, statt
still durchzulassen.
"""

from __future__ import annotations

from enum import Enum

from .auth import Principal


class Permission(str, Enum):
    AGENT_RUN = "agent:run"
    AGENT_CREATE = "agent:create"
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"
    APPROVAL_DECIDE = "approval:decide"
    BILLING_MANAGE = "billing:manage"
    TENANT_ADMIN = "tenant:admin"


#: Rolle → Rechte. Höhere Rollen erben implizit durch Aufzählung.
ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "viewer": frozenset({Permission.KNOWLEDGE_READ}),
    "member": frozenset({
        Permission.KNOWLEDGE_READ, Permission.KNOWLEDGE_WRITE, Permission.AGENT_RUN,
    }),
    "admin": frozenset({
        Permission.KNOWLEDGE_READ, Permission.KNOWLEDGE_WRITE, Permission.AGENT_RUN,
        Permission.AGENT_CREATE, Permission.APPROVAL_DECIDE,
    }),
    "owner": frozenset(Permission),  # alle Rechte
}


class PermissionDenied(Exception):
    pass


def permissions_of(principal: Principal) -> frozenset[Permission]:
    perms: set[Permission] = set()
    for role in principal.roles:
        perms |= ROLE_PERMISSIONS.get(role, frozenset())
    return frozenset(perms)


def has_permission(principal: Principal, permission: Permission) -> bool:
    return permission in permissions_of(principal)


def require(principal: Principal, permission: Permission) -> None:
    if not has_permission(principal, permission):
        raise PermissionDenied(
            f"{principal.subject or 'anon'} (Rollen {sorted(principal.roles)}) "
            f"hat kein Recht {permission.value}"
        )
