"""Gemeinsame Chat-Ausfuehrung fuer /v1/chat und Agenten (nicht-streamend UND
streamend). Erzwingt das Monats-Token-Limit, leitet an das LiteLLM-Gateway
weiter, persistiert Nachrichten + Verbrauch (mandantengebunden via RLS)."""
from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

import httpx
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from .auth import Principal
from .config import settings
from .db import tenant_tx
from .metrics import record_chat_usage
from .stripe_usage import report_usage

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
    Schliesst die TOCTOU-Luecke aus dem alten Vorab-Check: Postgres
    serialisiert konkurrierende UPDATEs auf dieselbe tenants-Zeile
    automatisch, eine zweite gleichzeitige Anfrage sieht die bereits
    erfolgte Reservierung der ersten, BEVOR sie selbst pruefen darf -- keine
    explizite Sperre noetig, kein Halten der Verbindung waehrend des
    (langsamen) externen Gateway-Aufrufs."""
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
    LiteLLM-Version, oder ein Stream ohne stream_options.include_usage).
    ~4 Zeichen/Token ist eine verbreitete Faustregel fuer lateinische Texte
    -- ungenau, aber weit besser als stillschweigend 0."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def _validate_conversation(tenant_id: str, conversation_id) -> None:
    """Prueft die Konversation VOR jeder Reservierung/jedem Gateway-Aufruf --
    eine falsche conversation_id soll nicht erst nach einem echten
    (kostenpflichtigen) LLM-Aufruf als 404 auffliegen."""
    if conversation_id is None:
        return
    with tenant_tx(tenant_id) as conn:
        owns = conn.execute(
            "SELECT 1 FROM conversations WHERE id = %s", (conversation_id,)
        ).fetchone()
    if owns is None:
        raise HTTPException(status_code=404, detail="Konversation nicht gefunden")


def _reserve_or_429(principal: Principal, prompt_text: str) -> int:
    """Reserviert atomar das geschaetzte Kontingent fuer diesen Aufruf und
    gibt den reservierten Betrag zurueck (zum spaeteren Freigeben). Wirft 429,
    wenn das Monats-Limit dadurch ueberschritten wuerde."""
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
    return reserve_estimate


def _persist_and_release(
    principal: Principal,
    conversation_id,
    last_user_message: str,
    model: str,
    answer: str,
    tokens_in: int,
    tokens_out: int,
    reserve_estimate: int,
):
    """Persistiert Nachrichten + Verbrauch und gibt die Reservierung in
    DERSELBEN Transaktion frei. Legt die Konversation an, falls neu."""
    with tenant_tx(principal.tenant_id) as conn:
        _release_reservation(conn, principal.tenant_id, reserve_estimate)

        if conversation_id is None:
            conversation_id = conn.execute(
                "INSERT INTO conversations (tenant_id) VALUES (%s) RETURNING id",
                (principal.tenant_id,),
            ).fetchone()["id"]

        conn.execute(
            "INSERT INTO messages (tenant_id, conversation_id, role, content, model) "
            "VALUES (%s,%s,'user',%s,%s)",
            (principal.tenant_id, conversation_id, last_user_message, model),
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
    return conversation_id


def _build_payload(model: str, out_messages: list[dict], tenant_id: str,
                    temperature: float | None, stream: bool) -> dict:
    payload = {"model": model, "messages": out_messages, "user": tenant_id}
    if temperature is not None:
        payload["temperature"] = temperature
    if stream:
        payload["stream"] = True
        # Bittet das Gateway, im letzten Stream-Chunk ein echtes usage-Objekt
        # mitzuschicken (OpenAI-kompatible Erweiterung, von LiteLLM
        # durchgereicht) -- ohne das muesste JEDE gestreamte Antwort geschaetzt
        # werden statt nur als Rueckfallebene.
        payload["stream_options"] = {"include_usage": True}
    return payload


def _gateway_headers() -> dict:
    headers = {}
    if settings.litellm_master_key:
        headers["Authorization"] = f"Bearer {settings.litellm_master_key}"
    return headers


async def run_chat(
    principal: Principal,
    model: str,
    messages: list[dict],
    conversation_id=None,
    system_prompt: str | None = None,
    temperature: float | None = None,
) -> dict:
    """Fuehrt eine NICHT-streamende Chat-Vervollstaendigung aus. `messages`
    sind bereits validierte Dicts ({role, content}). Modell-Validierung
    (registriert + Tarif) macht der Aufrufer."""
    _validate_conversation(principal.tenant_id, conversation_id)

    out_messages = messages
    if system_prompt:
        out_messages = [{"role": "system", "content": system_prompt}, *messages]
    prompt_text = "\n".join(m.get("content", "") for m in out_messages)
    reserve_estimate = _reserve_or_429(principal, prompt_text)

    payload = _build_payload(model, out_messages, principal.tenant_id, temperature, stream=False)
    headers = _gateway_headers()

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

    last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    conversation_id = _persist_and_release(
        principal, conversation_id, last_user, model, answer, tokens_in, tokens_out, reserve_estimate,
    )
    await report_usage(principal.stripe_customer_id, tokens_in + tokens_out)

    return {
        "conversation_id": str(conversation_id),
        "model": model,
        "answer": answer,
        "usage": {"tokens_in": tokens_in, "tokens_out": tokens_out},
    }


async def _stream_events(
    principal: Principal,
    model: str,
    messages: list[dict],
    conversation_id,
    out_messages: list[dict],
    prompt_text: str,
    reserve_estimate: int,
    temperature: float | None,
) -> AsyncIterator[bytes]:
    """Async-Generator: reicht die SSE-Chunks des Gateways an den Client
    durch, sammelt dabei den vollen Antworttext und das usage-Objekt (falls
    vorhanden) und persistiert NACH dem letzten Chunk -- exakt derselbe
    Reservierungs-/Freigabe-Mechanismus wie im nicht-streamenden Pfad,
    inklusive Freigabe bei jedem Fehlerausgang."""
    payload = _build_payload(model, out_messages, principal.tenant_id, temperature, stream=True)
    headers = _gateway_headers()

    answer_parts: list[str] = []
    tokens_in = tokens_out = 0
    usage_seen = False

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_s) as client:
            try:
                async with client.stream(
                    "POST", f"{settings.litellm_base_url}/v1/chat/completions",
                    json=payload, headers=headers,
                ) as resp:
                    if resp.status_code >= 400:
                        body = await resp.aread()
                        log.warning("Gateway-Fehler (stream) %s: %s", resp.status_code, body[:500])
                        raise HTTPException(status_code=502, detail="Upstream-Gateway-Fehler")

                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        chunk = line[len("data:"):].strip()
                        if chunk == "[DONE]":
                            yield b"data: [DONE]\n\n"
                            break
                        yield f"data: {chunk}\n\n".encode()
                        try:
                            obj = json.loads(chunk)
                        except json.JSONDecodeError:
                            continue
                        choices = obj.get("choices") or []
                        if choices:
                            delta = choices[0].get("delta", {}) or {}
                            piece = delta.get("content")
                            if piece:
                                answer_parts.append(piece)
                        if obj.get("usage"):
                            usage_seen = True
                            tokens_in = int(obj["usage"].get("prompt_tokens", 0))
                            tokens_out = int(obj["usage"].get("completion_tokens", 0))
            except httpx.HTTPError as exc:
                log.warning("Gateway nicht erreichbar (stream): %s", exc)
                raise HTTPException(status_code=502, detail="Upstream-Gateway nicht erreichbar")
    except Exception:
        with tenant_tx(principal.tenant_id) as conn:
            _release_reservation(conn, principal.tenant_id, reserve_estimate)
        # Der HTTP-Status ist bereits 200 (Stream laeuft) -- ein regulaerer
        # Fehler-Statuscode ist nicht mehr moeglich. Client sieht den
        # abgebrochenen Stream; der Fehler ist serverseitig geloggt und das
        # Kontingent korrekt freigegeben, nichts leckt.
        log.warning("Stream fuer Mandant %s abgebrochen", principal.tenant_id)
        return

    answer = "".join(answer_parts)
    if not usage_seen:
        tokens_in = _estimate_tokens(prompt_text)
        tokens_out = _estimate_tokens(answer)
        log.info(
            "Stream ohne usage-Objekt fuer Modell %s -- Tokens geschaetzt (in=%d, out=%d)",
            model, tokens_in, tokens_out,
        )

    last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    _persist_and_release(
        principal, conversation_id, last_user, model, answer, tokens_in, tokens_out, reserve_estimate,
    )
    await report_usage(principal.stripe_customer_id, tokens_in + tokens_out)


async def stream_chat(
    principal: Principal,
    model: str,
    messages: list[dict],
    conversation_id=None,
    system_prompt: str | None = None,
    temperature: float | None = None,
) -> StreamingResponse:
    """Wie run_chat, aber als Server-Sent-Events-Stream (OpenAI-kompatibles
    Chunk-Format, direkt vom Gateway durchgereicht). Validierung und
    Reservierung laufen VOR dem Erzeugen der StreamingResponse, damit ein
    429/404 noch als echter Statuscode ankommt (nach dem ersten gesendeten
    Byte ist der Statuscode fest auf 200)."""
    _validate_conversation(principal.tenant_id, conversation_id)

    out_messages = messages
    if system_prompt:
        out_messages = [{"role": "system", "content": system_prompt}, *messages]
    prompt_text = "\n".join(m.get("content", "") for m in out_messages)
    reserve_estimate = _reserve_or_429(principal, prompt_text)

    generator = _stream_events(
        principal, model, messages, conversation_id, out_messages,
        prompt_text, reserve_estimate, temperature,
    )
    return StreamingResponse(generator, media_type="text/event-stream")
