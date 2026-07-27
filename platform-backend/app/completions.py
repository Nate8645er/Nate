"""Gemeinsame Chat-Ausfuehrung fuer /v1/chat und Agenten (nicht-streamend UND
streamend). Erzwingt das Monats-Token-Limit, leitet an das LiteLLM-Gateway
weiter, persistiert Nachrichten + Verbrauch (mandantengebunden via RLS)."""
from __future__ import annotations

import asyncio
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
from .web_fetch_tool import MAX_RESULT_CHARS, WEB_FETCH_TOOL_SCHEMA, web_fetch

log = logging.getLogger("platform.completions")

# Harte Obergrenzen fuer den optionalen web_fetch-Tool-Aufruf im
# nicht-streamenden Chat-Pfad (run_chat) -- verhindert Endlosschleifen und
# unkontrollierte Gateway-Kosten, nicht nur per Kommentar dokumentiert.
# Nur der nicht-streamende Pfad bekommt das Tool: Tool-Calls im SSE-Format
# zu parsen ist deutlich komplexer und bleibt eine bewusste Einschraenkung
# dieser ersten Runde (siehe README).
MAX_TOOL_CALLS_PER_REQUEST = 3
MAX_GATEWAY_ROUNDS = 2


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

# Zusaetzlicher Puffer, wenn enable_web_tool=True: bis zu MAX_TOOL_CALLS_PER_REQUEST
# Tool-Ergebnisse (je bis zu MAX_RESULT_CHARS Zeichen, siehe web_fetch_tool.py)
# fliessen als zusaetzliche `role: tool`-Nachrichten in den ZWEITEN
# Gateway-Rundgang ein -- ohne diesen Puffer reserviert _RESPONSE_RESERVE_TOKENS
# allein systematisch zu wenig fuer genau diesen Fall. Grobe Schaetzung analog
# _estimate_tokens (~4 Zeichen/Token), bewusst grosszuegig statt exakt.
_WEB_TOOL_RESERVE_TOKENS = MAX_TOOL_CALLS_PER_REQUEST * MAX_RESULT_CHARS // 4

# Grobe, dokumentierte Pauschale pro Bild im Prompt (Vision-Anhaenge, siehe
# routes/chat.py): Bild-Content-Bloecke tragen 0 Zeichen zur zeichenbasierten
# _estimate_tokens-Schaetzung bei, verursachen bei den meisten Anbietern aber
# einen spuerbaren echten Tokenverbrauch (Groessenordnung abhaengig von
# Aufloesung/Anbieter). Ohne diesen Puffer wuerde eine Anfrage mit mehreren
# Bildern und wenig Text systematisch zu knapp reserviert, WENN das Gateway
# kein usage-Objekt liefert (der Normalfall liefert echte Nutzungsdaten und
# ersetzt diese Schaetzung sofort danach -- siehe _persist_and_release*).
_IMAGE_TOKEN_RESERVE_PER_IMAGE = 1500


def _count_images(messages: list[dict]) -> int:
    """Zaehlt `image_url`-Content-Bloecke ueber alle Nachrichten hinweg --
    fuer die Vorab-Token-Reservierung (siehe _IMAGE_TOKEN_RESERVE_PER_IMAGE)."""
    total = 0
    for m in messages:
        content = m.get("content")
        if isinstance(content, list):
            total += sum(1 for b in content if b.get("type") == "image_url")
    return total


def _stringify_content(content) -> str:
    """Wandelt ein Nachrichten-`content`-Feld (String ODER Liste multimodaler
    Content-Bloecke, siehe routes/chat.py) in reinen Text um -- fuer die
    zeichenbasierte Token-Schaetzung (_estimate_tokens) UND fuer die
    Persistenz in `messages.content` (DB-Spalte ist `text NOT NULL`, kann
    keine Bild-Binaerdaten aufnehmen -- und sollte es auch nicht, das waere
    unnoetiges Aufblaehen der Tabelle). Bild-Bloecke werden durch einen
    kurzen Platzhalter ersetzt, damit ihr Vorhandensein trotzdem sichtbar
    bleibt."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        n_images = 0
        for block in content:
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif block.get("type") == "image_url":
                n_images += 1
        if n_images:
            parts.append(f"[{n_images} Bild(er) angehaengt]")
        return "\n".join(p for p in parts if p)
    return ""


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


def _resolve_conversation_id(tenant_id: str, conversation_id):
    """Legt bei Bedarf sofort eine neue Konversation an, statt das erst am
    Streamende in _persist_and_release zu tun -- damit der Client die ID
    schon im ersten SSE-Chunk erfaehrt und Folgenachrichten wirklich an
    dieselbe Konversation anhaengen kann, statt bei jeder Nachricht neu
    anzufangen (vorher: die ID erreichte den Client im Stream-Pfad nie)."""
    if conversation_id is not None:
        return conversation_id
    with tenant_tx(tenant_id) as conn:
        return conn.execute(
            "INSERT INTO conversations (tenant_id) VALUES (%s) RETURNING id",
            (tenant_id,),
        ).fetchone()["id"]


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


def _reserve_or_429(
    principal: Principal,
    prompt_text: str,
    enable_web_tool: bool = False,
    extra_reserve_tokens: int = 0,
) -> int:
    """Reserviert atomar das geschaetzte Kontingent fuer diesen Aufruf und
    gibt den reservierten Betrag zurueck (zum spaeteren Freigeben). Wirft 429,
    wenn das Monats-Limit dadurch ueberschritten wuerde.

    `enable_web_tool=True` haengt _WEB_TOOL_RESERVE_TOKENS an die Reservierung
    an, weil in diesem Fall zusaetzliche Tool-Ergebnisse in den zweiten
    Gateway-Rundgang einfliessen koennen (siehe _WEB_TOOL_RESERVE_TOKENS).
    `extra_reserve_tokens` deckt weitere, vom Aufrufer bereits bezifferte
    Zusatzverbraeuche ab (aktuell: Bild-Anhaenge, siehe
    _IMAGE_TOKEN_RESERVE_PER_IMAGE/_count_images)."""
    reserve_estimate = (
        _estimate_tokens(prompt_text) + _RESPONSE_RESERVE_TOKENS + extra_reserve_tokens
    )
    if enable_web_tool:
        reserve_estimate += _WEB_TOOL_RESERVE_TOKENS
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


# README-dokumentierte Luecke: Persistenz-Fehler NACH einem erfolgreichen
# Gateway-Aufruf verlieren den Verbrauch (Kosten beim Anbieter sind bereits
# entstanden -- der Mandant hat das Modell wirklich benutzt, aber es wird nie
# abgerechnet/gezaehlt). Ein voller Outbox mit Wiederaufnahme ueber
# Prozessneustarts hinweg bleibt Phase 4 (braucht eine Queue). Diese
# Wiederholung deckt den haeufigeren Fall ab: einen kurzen, transienten
# DB-Fehler (Verbindungsabbruch, Pool-Erschoepfungsspitze) INNERHALB
# derselben Anfrage.
_PERSIST_RETRY_ATTEMPTS = 3
_PERSIST_RETRY_BACKOFF_S = 0.3


async def _persist_and_release_with_retry(
    principal: Principal,
    conversation_id,
    last_user_message: str,
    model: str,
    answer: str,
    tokens_in: int,
    tokens_out: int,
    reserve_estimate: int,
):
    last_exc: Exception | None = None
    for attempt in range(1, _PERSIST_RETRY_ATTEMPTS + 1):
        try:
            return _persist_and_release(
                principal, conversation_id, last_user_message, model,
                answer, tokens_in, tokens_out, reserve_estimate,
            )
        except Exception as exc:  # noqa: BLE001 -- jeder DB-Fehler ist hier ein Grund zum erneuten Versuch
            last_exc = exc
            log.warning(
                "Persistenz fehlgeschlagen (Versuch %d/%d) fuer Mandant %s: %s",
                attempt, _PERSIST_RETRY_ATTEMPTS, principal.tenant_id, exc,
            )
            if attempt < _PERSIST_RETRY_ATTEMPTS:
                await asyncio.sleep(_PERSIST_RETRY_BACKOFF_S * attempt)
    # Alle Versuche gescheitert: die Modellantwort ist real (Kosten beim
    # Anbieter sind entstanden), aber ohne Outbox nicht mehr rekonstruierbar.
    # Vollstaendig geloggt, damit es wenigstens manuell nachvollziehbar bleibt.
    log.error(
        "Persistenz endgueltig fehlgeschlagen nach %d Versuchen -- Mandant=%s Modell=%s "
        "tokens_in=%d tokens_out=%d Antwort (gekuerzt)=%r",
        _PERSIST_RETRY_ATTEMPTS, principal.tenant_id, model, tokens_in, tokens_out, answer[:200],
    )
    raise last_exc


def _build_payload(model: str, out_messages: list[dict], tenant_id: str,
                    temperature: float | None, stream: bool,
                    tools: list[dict] | None = None) -> dict:
    payload = {"model": model, "messages": out_messages, "user": tenant_id}
    if temperature is not None:
        payload["temperature"] = temperature
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
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


async def _post_gateway(payload: dict, headers: dict) -> dict:
    """Ein einzelner nicht-streamender Gateway-Rundgang. Wirft HTTPException
    bei Netzwerk-/Gateway-Fehlern -- gemeinsam genutzt vom ersten Aufruf und
    (falls das Modell Tool-Calls anfordert) vom zweiten Rundgang mit den
    Tool-Ergebnissen."""
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

    return resp.json()


async def _run_tool_calls(tool_calls: list[dict]) -> list[dict]:
    """Fuehrt bis zu MAX_TOOL_CALLS_PER_REQUEST angeforderte `web_fetch`-
    Tool-Calls tatsaechlich aus und baut die dazugehoerigen `role: tool`-
    Antwortnachrichten. Unbekannte Tool-Namen oder nicht parsebare Argumente
    fuehren zu einem Fehler-Tool-Ergebnis statt zu einem Crash -- das Modell
    bekommt so trotzdem eine Antwort, auf die es reagieren kann."""
    tool_messages: list[dict] = []
    for call in tool_calls[:MAX_TOOL_CALLS_PER_REQUEST]:
        call_id = call.get("id")
        fn = call.get("function", {}) or {}
        name = fn.get("name")
        if name != "web_fetch":
            content = f"Fehler: Unbekanntes Werkzeug '{name}'."
        else:
            try:
                args = json.loads(fn.get("arguments") or "{}")
                url = args["url"]
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                log.info("web_fetch Tool-Call mit ungueltigen Argumenten: %s", exc)
                content = "Fehler: Ungueltige Argumente fuer web_fetch."
            else:
                content = await web_fetch(url)
        tool_messages.append({"role": "tool", "tool_call_id": call_id, "content": content})
    return tool_messages


async def run_chat(
    principal: Principal,
    model: str,
    messages: list[dict],
    conversation_id=None,
    system_prompt: str | None = None,
    temperature: float | None = None,
    enable_web_tool: bool = False,
) -> dict:
    """Fuehrt eine NICHT-streamende Chat-Vervollstaendigung aus. `messages`
    sind bereits validierte Dicts ({role, content}). Modell-Validierung
    (registriert + Tarif) macht der Aufrufer.

    `enable_web_tool=True` haengt das `web_fetch`-Tool an (opt-in, siehe
    ChatRequest.enable_web_tool) -- Standardverhalten ohne das Flag ist exakt
    unveraendert. Fordert das Modell Tool-Calls an, werden sie serverseitig
    ausgefuehrt (SSRF-abgesichert, siehe web_fetch_tool.py) und das Gateway
    genau EIN zweites Mal aufgerufen (harte Obergrenze MAX_GATEWAY_ROUNDS),
    diesmal ohne Tools, um eine endgueltige Antwort zu erzwingen."""
    _validate_conversation(principal.tenant_id, conversation_id)

    out_messages = messages
    if system_prompt:
        out_messages = [{"role": "system", "content": system_prompt}, *messages]
    prompt_text = "\n".join(_stringify_content(m.get("content", "")) for m in out_messages)
    image_reserve = _count_images(messages) * _IMAGE_TOKEN_RESERVE_PER_IMAGE
    reserve_estimate = _reserve_or_429(principal, prompt_text, enable_web_tool, image_reserve)

    tools = [WEB_FETCH_TOOL_SCHEMA] if enable_web_tool else None
    headers = _gateway_headers()

    try:
        payload = _build_payload(
            model, out_messages, principal.tenant_id, temperature, stream=False, tools=tools,
        )
        data = await _post_gateway(payload, headers)
        message = data.get("choices", [{}])[0].get("message", {}) or {}
        usage = data.get("usage", {}) or {}
        tokens_in = int(usage.get("prompt_tokens", 0)) if usage else 0
        tokens_out = int(usage.get("completion_tokens", 0)) if usage else 0
        usage_seen = bool(usage)

        tool_calls = message.get("tool_calls") if enable_web_tool else None
        if tool_calls:
            tool_messages = await _run_tool_calls(tool_calls)
            # Zweiter (und letzter -- MAX_GATEWAY_ROUNDS=2) Rundgang: ohne
            # `tools`, damit das Modell eine endgueltige Antwort liefert statt
            # weitere Tool-Calls anzufordern, fuer die kein Budget mehr besteht.
            out_messages = [*out_messages, message, *tool_messages]
            payload2 = _build_payload(
                model, out_messages, principal.tenant_id, temperature, stream=False,
            )
            data = await _post_gateway(payload2, headers)
            message = data.get("choices", [{}])[0].get("message", {}) or {}
            usage2 = data.get("usage", {}) or {}
            if usage2:
                usage_seen = True
                tokens_in += int(usage2.get("prompt_tokens", 0))
                tokens_out += int(usage2.get("completion_tokens", 0))

        answer = message.get("content") or ""
        if not usage_seen:
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

    last_user = _stringify_content(
        next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    )
    conversation_id = await _persist_and_release_with_retry(
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

    # Erster Chunk, noch vor jeder Gateway-Antwort: die Konversations-ID, damit
    # der Client sie fuer die naechste Nachricht speichern kann (siehe
    # _resolve_conversation_id).
    yield f"data: {json.dumps({'conversation_id': str(conversation_id)})}\n\n".encode()

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

    last_user = _stringify_content(
        next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    )
    await _persist_and_release_with_retry(
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
    conversation_id = _resolve_conversation_id(principal.tenant_id, conversation_id)

    out_messages = messages
    if system_prompt:
        out_messages = [{"role": "system", "content": system_prompt}, *messages]
    prompt_text = "\n".join(_stringify_content(m.get("content", "")) for m in out_messages)
    image_reserve = _count_images(messages) * _IMAGE_TOKEN_RESERVE_PER_IMAGE
    reserve_estimate = _reserve_or_429(principal, prompt_text, extra_reserve_tokens=image_reserve)

    generator = _stream_events(
        principal, model, messages, conversation_id, out_messages,
        prompt_text, reserve_estimate, temperature,
    )
    return StreamingResponse(generator, media_type="text/event-stream")
