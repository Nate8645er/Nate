"""Gemeinsame Provisionierungs-Logik: Mandant + Owner + erster API-Schluessel.
Genutzt von der Admin-Route und vom Store-Webhook (orders/paid)."""
from __future__ import annotations

from fastapi import HTTPException

from .auth import generate_key
from .db import admin_tx


def provision_tenant(tenant_name: str, owner_email: str, plan_code: str) -> dict:
    """Legt Mandant, Owner-Nutzer und ersten API-Key an. Gibt den Klartext-Key
    genau einmal zurueck (danach nur der Hash in der DB)."""
    clear_key, key_hash = generate_key()

    with admin_tx() as conn:
        plan = conn.execute(
            "SELECT id FROM plans WHERE code = %s", (plan_code,)
        ).fetchone()
        if plan is None:
            raise HTTPException(status_code=400, detail=f"Tarif '{plan_code}' unbekannt")

        tenant_id = conn.execute(
            "INSERT INTO tenants (name, plan_id) VALUES (%s, %s) RETURNING id",
            (tenant_name, plan["id"]),
        ).fetchone()["id"]

        # users/api_keys sind RLS-geschuetzt; Mandantenkontext setzen, damit die
        # INSERTs die WITH CHECK-Policy erfuellen.
        conn.execute("SELECT set_config('app.current_tenant', %s, true)", (str(tenant_id),))
        conn.execute(
            "INSERT INTO users (tenant_id, email, role) VALUES (%s, %s, 'owner')",
            (tenant_id, owner_email),
        )
        conn.execute(
            "INSERT INTO api_keys (tenant_id, key_hash, label) VALUES (%s, %s, 'initial')",
            (tenant_id, key_hash),
        )

    return {"tenant_id": str(tenant_id), "plan": plan_code, "api_key": clear_key}
