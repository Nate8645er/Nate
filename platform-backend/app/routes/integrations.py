"""Integrations (Slack/Notion/Google) pro Mandant.

Echter OAuth-Flow ueber Composio, sobald COMPOSIO_API_KEY gesetzt ist
(composio_client.py): create_integration initiiert eine echte Verbindung
und liefert eine echte Login-URL zurueck; refresh_integration fragt den
echten Verbindungsstatus ab. Mandantentrennung (RLS) und das Tarif-Limit
(plans.max_integrations) sind unabhaengig davon durchgesetzt und getestet.

Ohne COMPOSIO_API_KEY (z.B. lokal ohne Composio-Account) bleibt das
bisherige Geruest-Verhalten erhalten: status bleibt beim Anlegen
'disconnected', kein Fehler, keine externe Anfrage.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from ..auth import Principal, require_principal
from ..composio_client import build_toolset, map_status
from ..db import admin_tx, tenant_tx

log = logging.getLogger("platform.integrations")

router = APIRouter()

KNOWN_PROVIDERS = {"slack", "notion", "google"}


class IntegrationCreate(BaseModel):
    provider: str = Field(min_length=1, max_length=50)
    config: dict = Field(default_factory=dict)
    redirect_url: str | None = Field(
        default=None,
        max_length=2000,
        description="Wohin Composio den Mandanten nach Abschluss des echten "
        "OAuth-Logins zurueckschickt. Ohne COMPOSIO_API_KEY ohne Wirkung.",
    )


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

    # Composio VOR dem Insert anstossen: schlaegt der externe Aufruf fehl,
    # soll gar keine Zeile entstehen, statt eine 'disconnected'-Integration
    # ohne jede Chance auf Verbindung anzulegen.
    connect_url: str | None = None
    config = dict(req.config)
    toolset = build_toolset()
    if toolset is not None:
        try:
            conn_req = toolset.initiate_connection(
                app=req.provider, redirect_url=req.redirect_url
            )
            config["composio_connected_account_id"] = conn_req.connectedAccountId
            connect_url = conn_req.redirectUrl
        except Exception as exc:  # Composio-SDK wirft diverse eigene Fehlertypen
            log.warning("Composio initiate_connection fehlgeschlagen: %s", exc)
            raise HTTPException(
                status_code=502,
                detail=f"Verbindung zu Composio fuer Provider '{req.provider}' "
                "fehlgeschlagen. Bitte spaeter erneut versuchen.",
            ) from exc

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
        # status bleibt 'disconnected' (DB-Default) bis refresh_integration
        # einen echten 'ACTIVE'-Status von Composio bestaetigt -- OHNE
        # Composio (toolset ist None) bleibt das dauerhaft so, exakt wie im
        # bisherigen Geruest.
        row = conn.execute(
            "INSERT INTO integrations (tenant_id, provider, config) "
            "VALUES (%s,%s,%s) "
            "RETURNING id, provider, status, config, created_at",
            (principal.tenant_id, req.provider, Jsonb(config)),
        ).fetchone()
    result = _serialize(row)
    result["connect_url"] = connect_url
    return result


@router.post("/v1/integrations/{integration_id}/refresh")
async def refresh_integration(
    integration_id: uuid.UUID, principal: Principal = Depends(require_principal)
):
    """Fragt den echten Verbindungsstatus bei Composio ab und aktualisiert
    `status` entsprechend. Ohne COMPOSIO_API_KEY oder ohne eine bei create
    hinterlegte Composio-Verbindung: klare 400 statt stillem No-Op."""
    with tenant_tx(principal.tenant_id) as conn:
        row = conn.execute(
            "SELECT id, provider, status, config, created_at FROM integrations "
            "WHERE id = %s",
            (integration_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Integration nicht gefunden")

        account_id = (row["config"] or {}).get("composio_connected_account_id")
        toolset = build_toolset()
        if toolset is None or not account_id:
            raise HTTPException(
                status_code=400,
                detail="Keine echte Composio-Verbindung fuer diese Integration "
                "hinterlegt (COMPOSIO_API_KEY fehlt oder Integration wurde vor "
                "der Composio-Anbindung angelegt).",
            )
        try:
            account = toolset.get_connected_account(account_id)
        except Exception as exc:
            log.warning("Composio get_connected_account fehlgeschlagen: %s", exc)
            raise HTTPException(
                status_code=502, detail="Statusabfrage bei Composio fehlgeschlagen."
            ) from exc

        new_status = map_status(account.status)
        row = conn.execute(
            "UPDATE integrations SET status = %s WHERE id = %s "
            "RETURNING id, provider, status, config, created_at",
            (new_status, integration_id),
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
