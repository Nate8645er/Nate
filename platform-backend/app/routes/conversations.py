"""Konversations-Historie (mandantengebunden via RLS). Fuer die Chat-UI:
Liste der Unterhaltungen + Nachrichten einer Unterhaltung."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from ..auth import Principal, require_principal
from ..db import tenant_tx

router = APIRouter()


@router.get("/v1/conversations")
async def list_conversations(principal: Principal = Depends(require_principal)):
    with tenant_tx(principal.tenant_id) as conn:
        rows = conn.execute(
            "SELECT id, title, created_at FROM conversations ORDER BY created_at DESC LIMIT 200"
        ).fetchall()
    return {
        "conversations": [
            {"id": str(r["id"]), "title": r["title"], "created_at": r["created_at"].isoformat()}
            for r in rows
        ]
    }


@router.get("/v1/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: uuid.UUID, principal: Principal = Depends(require_principal)
):
    with tenant_tx(principal.tenant_id) as conn:
        # RLS sorgt dafuer, dass nur eigene Konversationen sichtbar sind.
        conv = conn.execute(
            "SELECT id, title, created_at FROM conversations WHERE id = %s",
            (conversation_id,),
        ).fetchone()
        if conv is None:
            raise HTTPException(status_code=404, detail="Konversation nicht gefunden")
        msgs = conn.execute(
            "SELECT role, content, model, tokens_in, tokens_out, created_at "
            "FROM messages WHERE conversation_id = %s ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
    return {
        "id": str(conv["id"]),
        "title": conv["title"],
        "created_at": conv["created_at"].isoformat(),
        "messages": [
            {
                "role": m["role"],
                "content": m["content"],
                "model": m["model"],
                "tokens_in": m["tokens_in"],
                "tokens_out": m["tokens_out"],
                "created_at": m["created_at"].isoformat(),
            }
            for m in msgs
        ],
    }
