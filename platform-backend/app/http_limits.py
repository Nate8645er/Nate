"""Begrenzte Body-/Upload-Lektuere fuer Endpunkte, bei denen der komplette
Inhalt sonst VOR jeder Pruefung in den Speicher geladen wuerde (Webhooks,
Datei-Uploads).

`request.body()`/`UploadFile.read()` ohne Limit liest den kompletten Inhalt
in den Speicher, BEVOR irgendeine Pruefung (Signatur, Format etc.)
stattfindet — ein Aufrufer koennte beliebig grosse Bodies/Dateien senden und
den Prozess so in OOM treiben oder das Parsen ausbremsen. Eine reine
Content-Length-Pruefung reicht nicht: der Header kann fehlen oder luegen
(Chunked Transfer-Encoding). Deshalb wird hier gestreamt und beim
Ueberschreiten des Limits sofort abgebrochen.
"""
from __future__ import annotations

from fastapi import HTTPException, Request, UploadFile

# Echte Stripe-/Shopify-Webhook-Payloads liegen deutlich unter 1 MiB.
MAX_WEBHOOK_BODY_BYTES = 1_000_000

# Chunkgroesse fuer das gestreamte Lesen -- klein genug, dass ein Limit
# zuverlaessig nicht deutlich ueberschritten wird, gross genug fuer wenig
# Overhead bei normal grossen Dateien.
_READ_CHUNK_BYTES = 1024 * 1024


async def read_bounded_body(request: Request, limit: int = MAX_WEBHOOK_BODY_BYTES) -> bytes:
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > limit:
            raise HTTPException(status_code=413, detail="Body zu gross")
        chunks.append(chunk)
    return b"".join(chunks)


async def read_bounded_upload(file: UploadFile, limit: int) -> bytes:
    """Wie `read_bounded_body`, aber fuer multipart-Datei-Uploads
    (`UploadFile`, z.B. POST /v1/attachments/extract). Bricht mit 400 ab,
    sobald `limit` ueberschritten wird -- VOR jeder teureren Verarbeitung
    (z.B. PDF-Parsing)."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_READ_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise HTTPException(status_code=400, detail="Datei zu gross")
        chunks.append(chunk)
    return b"".join(chunks)
