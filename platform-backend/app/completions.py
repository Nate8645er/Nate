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
from .metrics import record_chat_usage

log = logging.getLogger("platform.completions")


def _month_usage(conn, tenant_id: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(tokens_in + tokens_out), 0) AS used "
        "FROM usage_events WHERE tenant_id = %s AND ts >= date_trunc('month', now())",
        (tenant_id,),
    ).fetchone()
    return int(row["used"])


# Fester Puffer, der zusaetzlich zum geschaetzten Prompt-Verbrauch reserviert
# wird -- deckt die Antwort ab, deren Laenge vor dem Gateway-Aufruf nicht
# bekannt ist. Bewusst eine grobe, dokumentierte Pauschale statt eines
# exakten Werts (den es vorab nicht geben kann); wird nach dem Aufruf sofort
# durch die echte (oder geschaetzte) Nutzung ersetzt.
_RESPONSE_RESERVE_TOKENS = 4000


def _reserve_tokens(conn, tenant_id: str, estimate: int, limit: int) -> bool:
    """Atomar: reserviert `estimate` Tokens, wenn (bereits verbrauchte +
    bereits reservierte + estimate) das Monats-Limit nicht ueberschreitet.
    Schliesst die TOCTOU-Luecke aus dem Vorab-Check (siehe README/Commit-
    Historie): Postgres serialisiert konkurrierende UPDATEs auf dieselbe
    tenants-Zeile automatisch, eine zweite gleichzeitige Anfrage sieht die
    bereits erfolgte Reservierung der ersten, BEVOR sie selbst pruefen darf
    -- keine explizite Sperre noetig, kein Halten der Verbindung waehrend des
    (langsamen) externen Gateway-Aufrufs (siehe run_chat)."""
    row = conn.execute(
        """
        UPDATE tenants t
        SET reserved_tokens = reserved_tokens + %(estimate)s
        WHERE t.id = %(tenant_id)s
          AND (
            COALESCE(
              (SELECT SUM(tokens_in + tokens_out) FROM usage_events
                WHERE tenant_id = t.id AND ts >= date_trunc('month', now())),
              0
            ) + t.reserved_tokens + %(estimate)s
          ) <= %(limit)s
        RETURNING t.id
        """,
        {"estimate": estimate, "tenant_id": tenant_id, "limit": limit},
    ).fetchone()
    return row is not None


def _release_reservation(conn, tenant_id: str, estimate: int) -> None:
    conn.execute(
        "UPDATE tenants SET reserved_tokens = GREATEST(0, reserved_tokens - %s) WHERE id = %s",
        (estimate, tenant_id),
    )


def _estimate_tokens(text: str) -> int:
    """Grobe Schaetzung ohne echten Tokenizer, NUR als Rueckfallebene wenn
    das Gateway kein usage-Objekt liefert (manche Ollama-Antworten je nach
    LiteLLM-Version). ~4 Zeichen/Token ist eine verbreitete Faustregel fuer
    lateinische Texte -- ungenau, aber weit besser als stillschweigend 0:
    ohne jede Schaetzung zaehlt dieser Verbrauch NIE gegen das Monats-Limit,
    ein Mandant koennte ueber ein Modell ohne usage-Objekt effektiv
    unbegrenzt und unverrechnet chatten."""
    if not text:
        return 0
    return max(1, len(text) // 4)


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
    # 1) Konversation validieren, BEVOR irgendein Kontingent reserviert oder
    # das (kostenpflichtige) Gateway kontaktiert wird -- eine falsche
    # conversation_id soll nicht erst nach einem echten LLM-Aufruf als 404
    # auffliegen.
    if conversation_id is not None:
        with tenant_tx(principal.tenant_id) as conn:
            owns = conn.execute(
                "SELECT 1 FROM conversations WHERE id = %s", (conversation_id,)
            ).fetchone()
        if owns is None:
            raise HTTPException(status_code=404, detail="Konversation nicht gefunden")

    # 2) Monats-Token-Limit -- ATOMAR reserviert (siehe _reserve_tokens),
    # nicht nur vorab geprueft. Die Reservierung wird NICHT waehrend des
    # externen Gateway-Aufrufs gehalten (kurze Transaktion, sofort committet)
    # -- sonst koennten mehrere langsame LLM-Aufrufe verschiedener Mandanten
    # den kleinen DB-Verbindungspool (max_size=10, siehe db.py) erschoepfen.
    out_messages = messages
    if system_prompt:
        out_messages = [{"role": "system", "content": system_prompt}, *messages]
    prompt_text = "\n".join(m.get("content", "") for m in out_messages)
    reserve_estimate = _estimate_tokens(prompt_text) + _RESPONSE_RESERVE_TOKENS

    with tenant_tx(principal.tenant_id) as conn:
        reserved = _reserve_tokens(
            conn, principal.tenant_id, reserve_estimate, principal.monthly_token_limit
        )
        if not reserved:
            used = _month_usage(conn, principal.tenant_id)
            raise HTTPException(
                status_code=429,
                detail=f"Monats-Token-Limit erreicht ({used}/{principal.monthly_token_limit})",
            )

    # 2) Weiterleitung ans Gateway. Reservierung MUSS bei jedem Ausgang
    # (Erfolg, Gateway-Fehler, Exception) freigegeben werden, sonst leckt
    # Kontingent dauerhaft.
    payload = {"model": model, "messages": out_messages, "user": principal.tenant_id}
    if temperature is not None:
        payload["temperature"] = temperature

    headers = {}
    if settings.litellm_master_key:
        headers["Authorization"] = f"Bearer {settings.litellm_master_key}"

    try:
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
        if usage:
            tokens_in = int(usage.get("prompt_tokens", 0))
            tokens_out = int(usage.get("completion_tokens", 0))
        else:
            # Kein usage-Objekt vom Gateway -- geschaetzt statt stillschweigend
            # 0 (siehe _estimate_tokens). Betrifft in der Praxis vor allem
            # lokale Modelle, deren Antwort nicht immer ein OpenAI-
            # kompatibles usage-Feld enthaelt.
            tokens_in = _estimate_tokens(prompt_text)
            tokens_out = _estimate_tokens(answer)
            log.info(
                "Gateway ohne usage-Objekt fuer Modell %s -- Tokens geschaetzt (in=%d, out=%d)",
                model, tokens_in, tokens_out,
            )
    except Exception:
        with tenant_tx(principal.tenant_id) as conn:
            _release_reservation(conn, principal.tenant_id, reserve_estimate)
        raise

    # 3) Persistenz (mandantengebunden) + Freigabe der Reservierung in
    # DERSELBEN Transaktion wie der echte Verbrauchseintrag. conversation_id
    # ist bereits validiert (Schritt 1) -- hier nur noch anlegen, falls neu.
    with tenant_tx(principal.tenant_id) as conn:
        _release_reservation(conn, principal.tenant_id, reserve_estimate)

        if conversation_id is None:
            conversation_id = conn.execute(
                "INSERT INTO conversations (tenant_id) VALUES (%s) RETURNING id",
                (principal.tenant_id,),
            ).fetchone()["id"]

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

    record_chat_usage(model, tokens_in, tokens_out)

    return {
        "conversation_id": str(conversation_id),
        "model": model,
        "answer": answer,
        "usage": {"tokens_in": tokens_in, "tokens_out": tokens_out},
    }
