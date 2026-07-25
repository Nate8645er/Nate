"""Gemeinsame Chat-Ausfuehrung fuer /v1/chat und Agenten. Erzwingt das
Monats-Token-Limit, leitet an das LiteLLM-Gateway weiter, persistiert
Nachrichten + Verbrauch (mandantengebunden via RLS)."""
from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException

from .auth import Principal
from .config import settings
from .db import tenant_tx

log = logging.getLogger("platform.completions")


def _month_usage(conn, tenant_id: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(tokens_in + tokens_out), 0) AS used "
        "FROM usage_events WHERE tenant_id = %s AND ts >= date_trunc('month', now())",
        (tenant_id,),
    ).fetchone()
    return int(row["used"])


async def run_chat(
    principal: Principal,
    model: str,
    messages: list[dict],
    conversation_id=None,
    system_prompt: str | None = None,
    temperature: float | None = None,
) -> dict:
    """Fuehrt eine Chat-Vervollstaendigung aus. `messages` sind bereits
    validierte Dicts ({role, content}). Modell-Validierung (registriert +
    Tarif) macht der Aufrufer."""
    # 1) Monats-Token-Limit.
    with tenant_tx(principal.tenant_id) as conn:
        used = _month_usage(conn, principal.tenant_id)
        if used >= principal.monthly_token_limit:
            raise HTTPException(
                status_code=429,
                detail=f"Monats-Token-Limit erreicht ({used}/{principal.monthly_token_limit})",
            )

    # 2) Weiterleitung ans Gateway. System-Prompt (Agent) ggf. voranstellen.
    out_messages = messages
    if system_prompt:
        out_messages = [{"role": "system", "content": system_prompt}, *messages]
    payload = {"model": model, "messages": out_messages, "user": principal.tenant_id}
    if temperature is not None:
        payload["temperature"] = temperature

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

    # 3) Persistenz (mandantengebunden).
    with tenant_tx(principal.tenant_id) as conn:
        if conversation_id is None:
            conversation_id = conn.execute(
                "INSERT INTO conversations (tenant_id) VALUES (%s) RETURNING id",
                (principal.tenant_id,),
            ).fetchone()["id"]
        else:
            owns = conn.execute(
                "SELECT 1 FROM conversations WHERE id = %s", (conversation_id,)
            ).fetchone()
            if owns is None:
                raise HTTPException(status_code=404, detail="Konversation nicht gefunden")

        last_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        conn.execute(
            "INSERT INTO messages (tenant_id, conversation_id, role, content, model) "
            "VALUES (%s,%s,'user',%s,%s)",
            (principal.tenant_id, conversation_id, last_user, model),
        )
        conn.execute(
            "INSERT INTO messages (tenant_id, conversation_id, role, content, model, tokens_in, tokens_out) "
            "VALUES (%s,%s,'assistant',%s,%s,%s,%s)",
            (principal.tenant_id, conversation_id, answer, model, tokens_in, tokens_out),
        )
        conn.execute(
            "INSERT INTO usage_events (tenant_id, model, tokens_in, tokens_out) "
            "VALUES (%s,%s,%s,%s)",
            (principal.tenant_id, model, tokens_in, tokens_out),
        )

    return {
        "conversation_id": str(conversation_id),
        "model": model,
        "answer": answer,
        "usage": {"tokens_in": tokens_in, "tokens_out": tokens_out},
    }
