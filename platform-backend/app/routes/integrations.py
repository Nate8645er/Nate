"""Integrations-Geruest (Slack/Notion/Google) pro Mandant.

WICHTIG -- ehrlicher Stand: Dies ist KEINE fertige Integration. Es gibt in
dieser Umgebung keine echten OAuth-Client-IDs/Secrets fuer Slack/Notion/
Google. Was hier korrekt und vollstaendig durchgesetzt und getestet ist:
Mandantentrennung (RLS) und das Tarif-Limit (plans.max_integrations). Was
FEHLT, bevor das eine echte Integration ist:

# TODO (echte Anbindung, noch offen):
#   - Echte OAuth-Client-IDs/Secrets pro Provider als Umgebungsvariablen
#     (z.B. SLACK_CLIENT_ID/SECRET, NOTION_CLIENT_ID/SECRET,
#     GOOGLE_CLIENT_ID/SECRET) -- existieren hier nicht.
#   - Ein /v1/integrations/{provider}/callback-Endpunkt, der den
#     OAuth-Code gegen ein Access-Token tauscht und status auf
#     'connected' setzt (aktuell gibt es dafuer keinen Aufrufer).
#   - Verschluesselte Token-Speicherung statt Klartext in `config`
#     (aktuell landet dort nur, was der Client selbst mitschickt).
#
# Solange das fehlt, bleibt `status` beim Anlegen IMMER 'disconnected'.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from ..auth import Principal, require_principal
from ..db import admin_tx, tenant_tx

router = APIRouter()

KNOWN_PROVIDERS = {"slack", "notion", "google"}


class IntegrationCreate(BaseModel):
    provider: str = Field(min_length=1, max_length=50)
    config: dict = Field(default_factory=dict)


def _serialize(r) -> dict:
    return {
        "id": str(r["id"]),
        "provider": r["provider"],
        "status": r["status"],
        "config": r["config"],
        "created_at": r["created_at"].isoformat(),
    }


@router.get("/v1/integrations")
async def list_integrations(principal: Principal = Depends(require_principal)):
    with tenant_tx(principal.tenant_id) as conn:
        rows = conn.execute(
            "SELECT id, provider, status, config, created_at "
            "FROM integrations ORDER BY created_at ASC"
        ).fetchall()
    return {
        "count": len(rows),
        "integrations": [_serialize(r) for r in rows],
    }


@router.post("/v1/integrations", status_code=201)
async def create_integration(
    req: IntegrationCreate, principal: Principal = Depends(require_principal)
):
    if req.provider not in KNOWN_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unbekannter Provider '{req.provider}' "
            f"(erlaubt: {', '.join(sorted(KNOWN_PROVIDERS))})",
        )

    # Tarif-Limit nachschlagen (tenants/plans sind nicht RLS-geschuetzt ->
    # admin_tx, analog zu billing_overview in app/routes/billing.py).
    with admin_tx() as conn:
        plan = conn.execute(
            "SELECT p.max_integrations FROM tenants t "
            "JOIN plans p ON p.id = t.plan_id WHERE t.id = %s",
            (principal.tenant_id,),
        ).fetchone()
    if plan is None:
        raise HTTPException(status_code=404, detail="Mandant nicht gefunden")
    max_integrations = int(plan["max_integrations"])

    with tenant_tx(principal.tenant_id) as conn:
        # Tarif-Limit durchsetzen (Count + Insert in derselben Transaktion,
        # sonst TOCTOU -- Muster wie bei app/routes/agents.py).
        count = conn.execute("SELECT count(*) AS c FROM integrations").fetchone()["c"]
        if count >= max_integrations:
            raise HTTPException(
                status_code=403,
                detail=f"Integrations-Limit des Tarifs {principal.plan_code} erreicht "
                f"({count}/{max_integrations})",
            )
        # status bleibt IMMER 'disconnected' -- es gibt keinen echten
        # OAuth-Callback, der ihn je auf 'connected' setzen wuerde (siehe
        # TODO im Modul-Docstring).
        row = conn.execute(
            "INSERT INTO integrations (tenant_id, provider, config) "
            "VALUES (%s,%s,%s) "
            "RETURNING id, provider, status, config, created_at",
            (principal.tenant_id, req.provider, Jsonb(req.config)),
        ).fetchone()
    return _serialize(row)


@router.delete("/v1/integrations/{integration_id}", status_code=204)
async def delete_integration(
    integration_id: uuid.UUID, principal: Principal = Depends(require_principal)
):
    with tenant_tx(principal.tenant_id) as conn:
        deleted = conn.execute(
            "DELETE FROM integrations WHERE id = %s RETURNING id", (integration_id,)
        ).fetchone()
    if deleted is None:
        raise HTTPException(status_code=404, detail="Integration nicht gefunden")
