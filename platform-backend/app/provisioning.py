"""Gemeinsame Provisionierungs-Logik: Mandant + Owner + erster API-Schluessel.
Genutzt von der Admin-Route, dem Store-Webhook und dem Stripe-Checkout."""
from __future__ import annotations

from fastapi import HTTPException

from .auth import generate_key
from .db import admin_tx


def _provision_in(conn, tenant_name: str, owner_email: str, plan_code: str) -> dict:
    clear_key, key_hash = generate_key()

    plan = conn.execute("SELECT id FROM plans WHERE code = %s", (plan_code,)).fetchone()
    if plan is None:
        raise HTTPException(status_code=400, detail=f"Tarif '{plan_code}' unbekannt")

    tenant_id = conn.execute(
        "INSERT INTO tenants (name, plan_id) VALUES (%s, %s) RETURNING id",
        (tenant_name, plan["id"]),
    ).fetchone()["id"]

    # users/api_keys sind RLS-geschuetzt; Mandantenkontext setzen, damit die
    # INSERTs die WITH CHECK-Policy erfuellen. is_local=true gilt fuer den
    # Rest DIESER Transaktion -- ruft ein Aufrufer (z.B. der Web-Signup in
    # app/routes/auth.py) mit einer eigenen offenen `conn` auf, bleibt der
    # Kontext auch fuer dessen NACHFOLGENDE Statements (z.B. password_hash
    # setzen) in derselben Transaktion gesetzt.
    conn.execute("SELECT set_config('app.current_tenant', %s, true)", (str(tenant_id),))
    user_id = conn.execute(
        "INSERT INTO users (tenant_id, email, role) VALUES (%s, %s, 'owner') RETURNING id",
        (tenant_id, owner_email),
    ).fetchone()["id"]
    conn.execute(
        "INSERT INTO api_keys (tenant_id, key_hash, label) VALUES (%s, %s, 'initial')",
        (tenant_id, key_hash),
    )
    return {
        "tenant_id": str(tenant_id),
        "user_id": str(user_id),
        "plan": plan_code,
        "api_key": clear_key,
    }


def provision_tenant(
    tenant_name: str, owner_email: str, plan_code: str, conn=None
) -> dict:
    """Legt Mandant, Owner-Nutzer und ersten API-Key an. Gibt den Klartext-Key
    genau einmal zurueck (danach nur der Hash in der DB).

    `conn`: optionale bestehende Transaktion. Webhooks uebergeben ihre
    Transaktion, damit Idempotenz-Belegung und Anlage EIN Commit sind.
    """
    if conn is not None:
        return _provision_in(conn, tenant_name, owner_email, plan_code)
    with admin_tx() as c:
        return _provision_in(c, tenant_name, owner_email, plan_code)
