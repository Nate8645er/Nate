"""Chat-Endpunkt. Validiert das Modell (registriert + Tarif) und delegiert die
Ausfuehrung an das gemeinsame completions.run_chat (Limit, Gateway, Persistenz,
Verbrauchsmessung)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import Principal, require_principal
from ..completions import run_chat
from ..models_catalog import is_registered
from ..plans import model_allowed
from ..ratelimit import chat_limiter

router = APIRouter()

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


def ensure_model_available(model: str, principal: Principal) -> None:
    """Modell muss am Gateway registriert UND im Tarif freigeschaltet sein.
    Klare 403 statt eines 502 vom Gateway."""
    if not is_registered(model):
        raise HTTPException(status_code=403, detail=f"Modell '{model}' ist nicht verfuegbar")
    if not model_allowed(model, principal.allowed_models):
        raise HTTPException(
            status_code=403,
            detail=f"Modell '{model}' ist im Tarif {principal.plan_code} nicht freigeschaltet",
        )


@router.post("/v1/chat")
async def chat(req: ChatRequest, principal: Principal = Depends(require_principal)):
    chat_limiter.check(principal.tenant_id)
    ensure_model_available(req.model, principal)
    return await run_chat(
        principal,
        model=req.model,
        messages=[m.model_dump() for m in req.messages],
        conversation_id=req.conversation_id,
        temperature=req.temperature,
    )
