"""Chat-Endpunkt. Validiert das Modell (registriert + Tarif) und delegiert die
Ausfuehrung an das gemeinsame completions.run_chat (Limit, Gateway, Persistenz,
Verbrauchsmessung)."""
from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from ..attachments import (
    MAX_IMAGE_BYTES,
    MAX_IMAGES_PER_MESSAGE,
    AttachmentError,
    validate_image_data_url,
)
from ..auth import Principal, require_principal
from ..completions import run_chat, stream_chat
from ..models_catalog import is_registered, supports_vision
from ..plans import model_allowed
from ..ratelimit import chat_limiter

router = APIRouter()

# Payload-Grenzen (DoS-Schutz). Ein authentifizierter Mandant kann sonst sehr
# grosse Bodies senden, die vor jeder Tarif-Pruefung im Speicher landen.
MAX_CONTENT_CHARS = 100_000
MAX_MESSAGES = 200
# Hoechstens so viele Content-Bloecke (Text+Bild kombiniert) pro Nachricht --
# eine reale Nachricht (etwas Text, ein paar Bilder) braucht davon nur eine
# Handvoll; verhindert, dass eine Nachricht aus tausenden winzigen Bloecken
# besteht.
MAX_CONTENT_BLOCKS = 8
# Base64 blaeht Binaerdaten um ~33% auf -- die Obergrenze fuer die Laenge des
# data:-URI-STRINGS muss daher groesser sein als das reine Byte-Limit
# (MAX_IMAGE_BYTES) aus app/attachments.py, plus etwas Puffer fuer den
# "data:image/...;base64,"-Praefix. Die tatsaechliche, verbindliche Pruefung
# der dekodierten Groesse macht validate_image_data_url() -- das hier ist nur
# eine grobe Vorab-Schranke gegen absurd lange Strings vor dem Base64-Decode.
_MAX_IMAGE_DATA_URL_CHARS = int(MAX_IMAGE_BYTES * 4 / 3) + 100


class TextContentBlock(BaseModel):
    type: Literal["text"]
    text: str = Field(max_length=MAX_CONTENT_CHARS)


class ImageUrlData(BaseModel):
    # OpenAI-kompatibles Format: {"url": "data:image/png;base64,..."}. Die
    # eigentliche Validierung (Base64, Groesse nach Decode, echte
    # Bild-Signatur) macht validate_image_data_url() in _validate_attachments
    # -- hier nur eine grobe Laengenschranke.
    url: str = Field(min_length=1, max_length=_MAX_IMAGE_DATA_URL_CHARS)


class ImageContentBlock(BaseModel):
    type: Literal["image_url"]
    image_url: ImageUrlData


ContentBlock = TextContentBlock | ImageContentBlock


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    # Rueckwaerts-kompatibel: content bleibt ein einfacher String KOENNEN
    # (bestehende Tests/Clients unveraendert), akzeptiert zusaetzlich eine
    # Liste multimodaler Content-Bloecke (OpenAI-kompatibles Format:
    # [{"type":"text","text":"..."}, {"type":"image_url","image_url":{"url":"data:..."}}]).
    content: str | list[ContentBlock]

    @field_validator("content")
    @classmethod
    def _validate_content(cls, v):
        if isinstance(v, str):
            if len(v) > MAX_CONTENT_CHARS:
                raise ValueError(f"Text ueberschreitet {MAX_CONTENT_CHARS} Zeichen")
            return v
        if not v:
            raise ValueError("content-Liste darf nicht leer sein")
        if len(v) > MAX_CONTENT_BLOCKS:
            raise ValueError(f"Zu viele Content-Bloecke (max {MAX_CONTENT_BLOCKS})")
        n_images = sum(1 for b in v if b.type == "image_url")
        if n_images > MAX_IMAGES_PER_MESSAGE:
            raise ValueError(f"Zu viele Bilder in einer Nachricht (max {MAX_IMAGES_PER_MESSAGE})")
        return v


class ChatRequest(BaseModel):
    model: str = Field(max_length=200)
    messages: list[ChatMessage] = Field(min_length=1, max_length=MAX_MESSAGES)
    conversation_id: uuid.UUID | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    stream: bool = False
    enable_web_tool: bool = Field(
        default=False,
        description="Opt-in: haengt das serverseitige web_fetch-Tool an (nur "
        "oeffentliche Seiten lesen, kein Login/Formulare/Aktionen). Nur "
        "wirksam wenn stream=False -- der SSE-Streaming-Pfad bekommt das "
        "Tool in dieser Runde nicht, das Feld wird dort ignoriert.",
    )


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


def validate_attachments(model: str, messages: list[ChatMessage]) -> None:
    """Bild-Content ist nur zulaessig, wenn `model` Vision unterstuetzt --
    sonst eine klare 400-Fehlermeldung statt eines stillschweigenden
    Ignorierens oder Weiterreichens an ein Modell, das damit nicht umgehen
    kann. Jedes Bild wird zusaetzlich vollstaendig validiert (Base64,
    Groessenlimit nach Decode, echte Magic-Byte-Signatur statt des blossen
    behaupteten MIME-Praefixes) -- siehe app/attachments.py. Laeuft VOR jeder
    Token-Reservierung/jedem Gateway-Aufruf, analog zu ensure_model_available.

    OEFFENTLICH (kein fuehrender Unterstrich): `app/routes/agents.py` nutzt
    dieselbe `ChatMessage`-Klasse fuer `/v1/agents/{id}/chat` und MUSS
    dieselbe Pruefung durchlaufen -- sonst koennten Bild-Anhaenge dort
    unvalidiert (kein Vision-Check, keine Groessen-/Signaturpruefung) an das
    Gateway durchgereicht werden."""
    has_image = any(
        isinstance(m.content, list) and any(b.type == "image_url" for b in m.content)
        for m in messages
    )
    if has_image and not supports_vision(model):
        raise HTTPException(
            status_code=400,
            detail=f"Modell '{model}' unterstuetzt keine Bild-Eingabe",
        )
    for m in messages:
        if not isinstance(m.content, list):
            continue
        for block in m.content:
            if isinstance(block, ImageContentBlock):
                try:
                    validate_image_data_url(block.image_url.url)
                except AttachmentError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/v1/chat")
async def chat(req: ChatRequest, principal: Principal = Depends(require_principal)):
    chat_limiter.check(principal.tenant_id)
    ensure_model_available(req.model, principal)
    validate_attachments(req.model, req.messages)
    if req.stream:
        return await stream_chat(
            principal,
            model=req.model,
            messages=[m.model_dump() for m in req.messages],
            conversation_id=req.conversation_id,
            temperature=req.temperature,
        )
    return await run_chat(
        principal,
        model=req.model,
        messages=[m.model_dump() for m in req.messages],
        conversation_id=req.conversation_id,
        temperature=req.temperature,
        enable_web_tool=req.enable_web_tool,
    )
