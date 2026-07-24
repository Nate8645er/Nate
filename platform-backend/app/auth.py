"""Authentifizierung ueber mandantengebundene API-Schluessel.

Der Client sendet `Authorization: Bearer <klartext-key>`. Gespeichert wird
nur der SHA-256-Hash. Der Lookup liefert Mandant + Tarif; damit steht der
Mandantenkontext fuer den Rest der Anfrage fest.
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

from fastapi import Header, HTTPException


@dataclass
class Principal:
    tenant_id: str
    tenant_name: str
    plan_code: str
    allowed_models: list
    monthly_token_limit: int
    max_agents: int
    status: str


def hash_key(clear: str) -> str:
    return hashlib.sha256(clear.encode("utf-8")).hexdigest()


def generate_key() -> tuple[str, str]:
    """Erzeugt (klartext, hash). Klartext wird dem Kunden genau einmal gezeigt."""
    clear = "pk_" + secrets.token_urlsafe(32)
    return clear, hash_key(clear)


async def require_principal(
    authorization: str = Header(default=""),
) -> Principal:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer-Token fehlt")
    token = authorization[7:].strip()
    key_hash = hash_key(token)

    from .db import admin_tx  # lazy: haelt dieses Modul ohne DB importierbar

    # Lookup laeuft ueber admin_tx (api_keys-Join braucht Tenant-uebergreifende
    # Sicht auf genau diese eine Zeile; RLS wuerde sich sonst selbst blockieren,
    # weil der Mandant erst hier bestimmt wird).
    with admin_tx() as conn:
        row = conn.execute(
            """
            SELECT t.id AS tenant_id, t.name AS tenant_name, t.status AS status,
                   p.code AS plan_code, p.allowed_models, p.monthly_token_limit,
                   p.max_agents
            FROM api_keys k
            JOIN tenants t ON t.id = k.tenant_id
            JOIN plans   p ON p.id = t.plan_id
            WHERE k.key_hash = %s
            """,
            (key_hash,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="Ungueltiger API-Schluessel")
        conn.execute(
            "UPDATE api_keys SET last_used_at = now() WHERE key_hash = %s", (key_hash,)
        )

    if row["status"] != "active":
        raise HTTPException(status_code=403, detail=f"Mandant {row['status']}")

    return Principal(
        tenant_id=str(row["tenant_id"]),
        tenant_name=row["tenant_name"],
        plan_code=row["plan_code"],
        allowed_models=row["allowed_models"],
        monthly_token_limit=int(row["monthly_token_limit"]),
        max_agents=int(row["max_agents"]),
        status=row["status"],
    )
