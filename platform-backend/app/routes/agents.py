"""Agenten-Verwaltung pro Mandant. Die Anzahl ist tarifgebunden
(plans.max_agents) und wird beim Anlegen durchgesetzt."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import Principal, require_principal
from ..db import tenant_tx
from ..models_catalog import is_registered
from ..plans import model_allowed

router = APIRouter()


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    model: str = Field(max_length=200)
    system_prompt: str = Field(default="", max_length=20_000)


def _serialize(r) -> dict:
    return {
        "id": str(r["id"]),
        "name": r["name"],
        "model": r["model"],
        "system_prompt": r["system_prompt"],
        "created_at": r["created_at"].isoformat(),
    }


@router.get("/v1/agents")
async def list_agents(principal: Principal = Depends(require_principal)):
    with tenant_tx(principal.tenant_id) as conn:
        rows = conn.execute(
            "SELECT id, name, model, system_prompt, created_at "
            "FROM agents ORDER BY created_at ASC"
        ).fetchall()
    return {
        "max_agents": principal.max_agents,
        "count": len(rows),
        "agents": [_serialize(r) for r in rows],
    }


@router.post("/v1/agents", status_code=201)
async def create_agent(
    req: AgentCreate, principal: Principal = Depends(require_principal)
):
    # Modell muss registriert UND im Tarif freigeschaltet sein.
    if not is_registered(req.model):
        raise HTTPException(status_code=403, detail=f"Modell '{req.model}' ist nicht verfuegbar")
    if not model_allowed(req.model, principal.allowed_models):
        raise HTTPException(
            status_code=403,
            detail=f"Modell '{req.model}' ist im Tarif {principal.plan_code} nicht freigeschaltet",
        )

    with tenant_tx(principal.tenant_id) as conn:
        # Tarif-Limit durchsetzen (Count + Insert in derselben Transaktion).
        count = conn.execute("SELECT count(*) AS c FROM agents").fetchone()["c"]
        if count >= principal.max_agents:
            raise HTTPException(
                status_code=403,
                detail=f"Agenten-Limit des Tarifs {principal.plan_code} erreicht "
                f"({count}/{principal.max_agents})",
            )
        row = conn.execute(
            "INSERT INTO agents (tenant_id, name, model, system_prompt) "
            "VALUES (%s,%s,%s,%s) "
            "RETURNING id, name, model, system_prompt, created_at",
            (principal.tenant_id, req.name, req.model, req.system_prompt),
        ).fetchone()
    return _serialize(row)


@router.get("/v1/agents/{agent_id}")
async def get_agent(
    agent_id: uuid.UUID, principal: Principal = Depends(require_principal)
):
    with tenant_tx(principal.tenant_id) as conn:
        row = conn.execute(
            "SELECT id, name, model, system_prompt, created_at FROM agents WHERE id = %s",
            (agent_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Agent nicht gefunden")
    return _serialize(row)


@router.delete("/v1/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: uuid.UUID, principal: Principal = Depends(require_principal)
):
    with tenant_tx(principal.tenant_id) as conn:
        deleted = conn.execute(
            "DELETE FROM agents WHERE id = %s RETURNING id", (agent_id,)
        ).fetchone()
    if deleted is None:
        raise HTTPException(status_code=404, detail="Agent nicht gefunden")
