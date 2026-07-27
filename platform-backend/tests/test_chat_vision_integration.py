"""Beweist die Bild-Anhang-Validierung im /v1/chat-Pfad gegen eine echte
Postgres-DB, mit einem gefaelschten (nicht-streamenden) Gateway. Die
SSRF-/Bild-Sniffing-Logik selbst wird hier NICHT erneut auf jeden Edge-Case
geprueft -- das leistet bereits tests/test_attachments.py -- sondern nur die
Orchestrierung: Vision-Modell-Pflicht, 400 statt stillem Ignorieren/502,
Rueckwaerts-Kompatibilitaet des reinen String-content-Felds."""
from __future__ import annotations

import base64
import os

import httpx
import pytest

from app.attachments import MAX_IMAGE_BYTES

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)

# Kleinstmoegliches gueltiges PNG (1x1 Pixel) -- echte Magic-Bytes.
TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

# Im "pro"-Tarif freigeschaltet (migrations/002_seed_plans.sql): ein
# Vision-Modell (Claude Sonnet 5, vision=True) UND ein Nicht-Vision-Modell
# (Llama 3.2 lokal, vision=False) -- siehe app/models_catalog.py.
VISION_MODEL = "anthropic/claude-sonnet-5"
NON_VISION_MODEL = "ollama/llama3.2"


class _QueuedGateway:
    """Fake fuer httpx.AsyncClient (nicht-streamender .post()-Pfad) --
    zeichnet den gesendeten Payload auf und beantwortet der Reihe nach."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests: list[dict] = []

    def __call__(self, *a, **kw):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, json=None, headers=None):  # noqa: A002
        self.requests.append(json)
        body = self.responses.pop(0)
        return httpx.Response(200, json=body)


def _image_message(text: str, image_b64: str = TINY_PNG_B64, mime: str = "image/png"):
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
        ],
    }


def test_image_accepted_by_vision_model(client, prov, monkeypatch):
    fake = _QueuedGateway([
        {
            "choices": [{"message": {"role": "assistant", "content": "Ich sehe ein Bild."}}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 5},
        },
    ])
    monkeypatch.setattr("app.completions.httpx.AsyncClient", fake)

    prov("pro")
    r = client.post(
        "/v1/chat",
        json={
            "model": VISION_MODEL,
            "messages": [_image_message("Was siehst du auf diesem Bild?")],
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["answer"] == "Ich sehe ein Bild."

    # Der Bild-Content-Block wurde unveraendert (OpenAI-kompatibles Format)
    # an das Gateway durchgereicht.
    sent = fake.requests[0]["messages"][0]
    assert sent["content"][1]["type"] == "image_url"
    assert sent["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_image_rejected_by_non_vision_model(client, prov, monkeypatch):
    fake = _QueuedGateway([])
    monkeypatch.setattr("app.completions.httpx.AsyncClient", fake)

    prov("pro")
    r = client.post(
        "/v1/chat",
        json={
            "model": NON_VISION_MODEL,
            "messages": [_image_message("Was siehst du auf diesem Bild?")],
        },
    )
    assert r.status_code == 400, r.text
    assert "unterstuetzt keine Bild-Eingabe" in r.json()["detail"]
    assert NON_VISION_MODEL in r.json()["detail"]
    # Kein Gateway-Aufruf -- die Ablehnung passiert VOR jedem Upstream-Call.
    assert fake.requests == []


def test_oversized_image_is_rejected_with_400(client, prov, monkeypatch):
    fake = _QueuedGateway([])
    monkeypatch.setattr("app.completions.httpx.AsyncClient", fake)

    raw = b"\x89PNG\r\n\x1a\n" + b"\x00" * (MAX_IMAGE_BYTES + 1)
    big_b64 = base64.b64encode(raw).decode()

    prov("pro")
    r = client.post(
        "/v1/chat",
        json={
            "model": VISION_MODEL,
            "messages": [_image_message("Zu gross", image_b64=big_b64)],
        },
    )
    assert r.status_code == 400, r.text
    assert "Groessenlimit" in r.json()["detail"]
    assert fake.requests == []


def test_fake_mime_signature_is_rejected_with_400(client, prov, monkeypatch):
    """Text-Bytes mit einem behaupteten data:image/png-Praefix duerfen nicht
    als Bild an das Gateway durchgereicht werden."""
    fake = _QueuedGateway([])
    monkeypatch.setattr("app.completions.httpx.AsyncClient", fake)

    fake_payload_b64 = base64.b64encode(b"Das hier ist nur Text, kein Bild.").decode()

    prov("pro")
    r = client.post(
        "/v1/chat",
        json={
            "model": VISION_MODEL,
            "messages": [_image_message("Gefaelscht", image_b64=fake_payload_b64)],
        },
    )
    assert r.status_code == 400, r.text
    assert "kein erkennbares Bild" in r.json()["detail"]
    assert fake.requests == []


def test_invalid_base64_is_rejected_with_400_not_crash(client, prov, monkeypatch):
    fake = _QueuedGateway([])
    monkeypatch.setattr("app.completions.httpx.AsyncClient", fake)

    prov("pro")
    r = client.post(
        "/v1/chat",
        json={
            "model": VISION_MODEL,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Kaputt"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,!!!nicht-base64!!!"},
                    },
                ],
            }],
        },
    )
    assert r.status_code == 400, r.text
    assert fake.requests == []


def test_too_many_images_per_message_is_rejected(client, prov, monkeypatch):
    fake = _QueuedGateway([])
    monkeypatch.setattr("app.completions.httpx.AsyncClient", fake)

    blocks = [{"type": "text", "text": "Fuenf Bilder"}] + [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{TINY_PNG_B64}"}}
        for _ in range(5)
    ]

    prov("pro")
    r = client.post(
        "/v1/chat",
        json={"model": VISION_MODEL, "messages": [{"role": "user", "content": blocks}]},
    )
    assert r.status_code == 422, r.text  # strukturelle Pydantic-Grenze, siehe routes/chat.py
    assert fake.requests == []


def test_plain_string_content_still_works_unchanged(client, prov, monkeypatch):
    """Rueckwaerts-Kompatibilitaet: der bisherige reine String-content-Pfad
    ist durch die neue Union-Typisierung unveraendert."""
    fake = _QueuedGateway([
        {
            "choices": [{"message": {"role": "assistant", "content": "Hallo!"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 3},
        },
    ])
    monkeypatch.setattr("app.completions.httpx.AsyncClient", fake)

    prov("pro")
    r = client.post(
        "/v1/chat",
        json={"model": NON_VISION_MODEL, "messages": [{"role": "user", "content": "Hallo"}]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["answer"] == "Hallo!"
    assert fake.requests[0]["messages"][0]["content"] == "Hallo"
