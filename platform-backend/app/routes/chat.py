"""Chat-Endpunkt. Leitet an das LiteLLM-Gateway weiter und erzwingt dabei
die Tarif-Regeln: erlaubte Modelle + Monats-Token-Limit. Misst den Verbrauch
pro Mandant (Grundlage der Abrechnung)."""
from __future__ import annotations

import logging
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import Principal, require_principal
from ..config import settings
from ..db import tenant_tx
from ..plans import model_allowed

router = APIRouter()
log = logging.getLogger("platform.chat")

# Payload-Grenzen (DoS-Schutz). Ein authentifizierter Mandant kann sonst sehr
# grosse Bodies senden, die vor jeder Tarif-Pruefung im Speicher landen.
MAX_CONTENT_CHARS = 100_000
MAX_MESSAGES = 200


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str = Field(max_length=MAX_CONTENT_CHARS)


class ChatRequest(BaseModel):
    model: str = Field(max_length=200)
    messages: list[ChatMessage] = Field(min_length=1, max_length=MAX_MESSAGES)
    conversation_id: uuid.UUID | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)


def _month_usage(conn, tenant_id: str) -> int:
    row = conn.execute(
        """
        SELECT COALESCE(SUM(tokens_in + tokens_out), 0) AS used
        FROM usage_events
        WHERE tenant_id = %s AND ts >= date_trunc('month', now())
        """,
        (tenant_id,),
    ).fetchone()
    return int(row["used"])


@router.post("/v1/chat")
async def chat(req: ChatRequest, principal: Principal = Depends(require_principal)):
    # 1) Tarif: Modell freigeschaltet?
    if not model_allowed(req.model, principal.allowed_models):
        raise HTTPException(
            status_code=403,
            detail=f"Modell '{req.model}' ist im Tarif {principal.plan_code} nicht freigeschaltet",
        )

    # 2) Tarif: Monats-Token-Limit noch nicht ueberschritten?
    with tenant_tx(principal.tenant_id) as conn:
        used = _month_usage(conn, principal.tenant_id)
        if used >= principal.monthly_token_limit:
            raise HTTPException(
                status_code=429,
                detail=f"Monats-Token-Limit erreicht ({used}/{principal.monthly_token_limit})",
            )

    # 3) Weiterleitung an LiteLLM (OpenAI-kompatibel). `user` = Mandant, damit
    #    das Gateway den Verbrauch ebenfalls dem Mandanten zuordnen kann.
    payload = {
        "model": req.model,
        "messages": [m.model_dump() for m in req.messages],
        "user": principal.tenant_id,
    }
    if req.temperature is not None:
        payload["temperature"] = req.temperature

    headers = {}
    if settings.litellm_master_key:
        headers["Authorization"] = f"Bearer {settings.litellm_master_key}"

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_s) as client:
            resp = await client.post(
                f"{settings.litellm_base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            )
    except httpx.HTTPError as exc:
        # Detail nur ins Server-Log, generische Meldung an den Client (kein
        # Leak interner Hostnamen/Provider-Rohfehler).
        log.warning("Gateway nicht erreichbar: %s", exc)
        raise HTTPException(status_code=502, detail="Upstream-Gateway nicht erreichbar")

    if resp.status_code >= 400:
        log.warning("Gateway-Fehler %s: %s", resp.status_code, resp.text[:500])
        raise HTTPException(status_code=502, detail="Upstream-Gateway-Fehler")

    data = resp.json()
    answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    usage = data.get("usage", {}) or {}
    tokens_in = int(usage.get("prompt_tokens", 0))
    tokens_out = int(usage.get("completion_tokens", 0))

    # 4) Verbrauch + Nachrichten persistieren (mandantengebunden via RLS).
    with tenant_tx(principal.tenant_id) as conn:
        conv_id = req.conversation_id
        if conv_id is None:
            conv_id = conn.execute(
                "INSERT INTO conversations (tenant_id) VALUES (%s) RETURNING id",
                (principal.tenant_id,),
            ).fetchone()["id"]
        else:
            # Eigentum pruefen: die Konversation muss dem Mandanten gehoeren.
            # (RLS filtert bereits auf den Mandanten; das SELECT sieht die Zeile
            # also nur, wenn sie wirklich diesem Mandanten gehoert.)
            owns = conn.execute(
                "SELECT 1 FROM conversations WHERE id = %s", (conv_id,)
            ).fetchone()
            if owns is None:
                raise HTTPException(status_code=404, detail="Konversation nicht gefunden")
        last_user = next(
            (m.content for m in reversed(req.messages) if m.role == "user"), ""
        )
        conn.execute(
            "INSERT INTO messages (tenant_id, conversation_id, role, content, model) "
            "VALUES (%s,%s,'user',%s,%s)",
            (principal.tenant_id, conv_id, last_user, req.model),
        )
        conn.execute(
            "INSERT INTO messages (tenant_id, conversation_id, role, content, model, tokens_in, tokens_out) "
            "VALUES (%s,%s,'assistant',%s,%s,%s,%s)",
            (principal.tenant_id, conv_id, answer, req.model, tokens_in, tokens_out),
        )
        conn.execute(
            "INSERT INTO usage_events (tenant_id, model, tokens_in, tokens_out) "
            "VALUES (%s,%s,%s,%s)",
            (principal.tenant_id, req.model, tokens_in, tokens_out),
        )

    return {
        "conversation_id": str(conv_id),
        "model": req.model,
        "answer": answer,
        "usage": {"tokens_in": tokens_in, "tokens_out": tokens_out},
    }
