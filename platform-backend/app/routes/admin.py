"""Provisionierung: Mandant anlegen + ersten API-Schluessel ausgeben.

Geschuetzt durch einen Admin-Token (Umgebungsvariable ADMIN_TOKEN). Genau
diesen Endpunkt ruft spaeter der Store-Webhook `orders/paid` auf, um nach
einem Kauf automatisch einen Mandanten freizuschalten (Master-Prompt 4.2).
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr

from ..auth import generate_key
from ..db import admin_tx

router = APIRouter()


def _require_admin(x_admin_token: str) -> None:
    expected = os.environ.get("ADMIN_TOKEN", "")
    # Konstante-Zeit-Vergleich, und leerer/nicht gesetzter Token sperrt alles.
    import hmac

    if not expected or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Admin-Token ungueltig")


class ProvisionRequest(BaseModel):
    tenant_name: str
    owner_email: EmailStr
    plan_code: str


@router.post("/admin/provision")
async def provision(
    req: ProvisionRequest, x_admin_token: str = Header(default="")
):
    _require_admin(x_admin_token)
    clear_key, key_hash = generate_key()

    with admin_tx() as conn:
        plan = conn.execute(
            "SELECT id FROM plans WHERE code = %s", (req.plan_code,)
        ).fetchone()
        if plan is None:
            raise HTTPException(status_code=400, detail=f"Tarif '{req.plan_code}' unbekannt")

        tenant_id = conn.execute(
            "INSERT INTO tenants (name, plan_id) VALUES (%s, %s) RETURNING id",
            (req.tenant_name, plan["id"]),
        ).fetchone()["id"]

        # users/api_keys sind RLS-geschuetzt; hier wird der Mandantenkontext
        # gesetzt, damit die INSERTs die WITH CHECK-Policy erfuellen.
        conn.execute("SELECT set_config('app.current_tenant', %s, true)", (str(tenant_id),))
        conn.execute(
            "INSERT INTO users (tenant_id, email, role) VALUES (%s, %s, 'owner')",
            (tenant_id, req.owner_email),
        )
        conn.execute(
            "INSERT INTO api_keys (tenant_id, key_hash, label) VALUES (%s, %s, 'initial')",
            (tenant_id, key_hash),
        )

    # Klartext-Key genau einmal zurueckgeben — danach nur noch der Hash in der DB.
    return {
        "tenant_id": str(tenant_id),
        "plan": req.plan_code,
        "api_key": clear_key,
        "note": "Diesen Schluessel sicher speichern — er wird nicht erneut angezeigt.",
    }
