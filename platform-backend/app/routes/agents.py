"""Agenten-Verwaltung pro Mandant. Die Anzahl ist tarifgebunden
(plans.max_agents) und wird beim Anlegen durchgesetzt."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import Principal, require_principal
from ..completions import run_chat, stream_chat
from ..db import tenant_tx
from ..models_catalog import is_registered
from ..plans import model_allowed
from ..ratelimit import chat_limiter
from .chat import MAX_MESSAGES, ChatMessage, ensure_model_available, validate_attachments

router = APIRouter()


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    model: str = Field(max_length=200)
    system_prompt: str = Field(default="", max_length=20_000)


class AgentChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=MAX_MESSAGES)
    conversation_id: uuid.UUID | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    stream: bool = False


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


@router.post("/v1/agents/{agent_id}/chat")
async def run_agent(
    agent_id: uuid.UUID,
    req: AgentChatRequest,
    principal: Principal = Depends(require_principal),
):
    """Fuehrt den Agenten aus: sein System-Prompt + sein Modell, ansonsten die
    gemeinsame Chat-Bahn (Limit, Gateway, Persistenz, Verbrauch)."""
    chat_limiter.check(principal.tenant_id)
    with tenant_tx(principal.tenant_id) as conn:
        agent = conn.execute(
            "SELECT model, system_prompt FROM agents WHERE id = %s", (agent_id,)
        ).fetchone()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent nicht gefunden")

    # Das Agentenmodell kann seit dem Anlegen aus dem Tarif gefallen sein -> pruefen.
    ensure_model_available(agent["model"], principal)
    # Dieselbe Bild-Anhang-Validierung wie /v1/chat (Vision-Pflicht,
    # Groessen-/Signaturpruefung) -- AgentChatRequest.messages nutzt dieselbe
    # multimodale ChatMessage-Klasse, s. app/routes/chat.py.
    validate_attachments(agent["model"], req.messages)

    if req.stream:
        return await stream_chat(
            principal,
            model=agent["model"],
            messages=[m.model_dump() for m in req.messages],
            conversation_id=req.conversation_id,
            system_prompt=agent["system_prompt"],
            temperature=req.temperature,
        )
    return await run_chat(
        principal,
        model=agent["model"],
        messages=[m.model_dump() for m in req.messages],
        conversation_id=req.conversation_id,
        system_prompt=agent["system_prompt"],
        temperature=req.temperature,
    )
