"""Begrenzte Body-Lektuere fuer unauthentifizierte Endpunkte (Webhooks).

`request.body()` liest den kompletten Body in den Speicher, BEVOR irgendeine
Pruefung (Signatur etc.) stattfindet — ein anonymer Aufrufer koennte beliebig
grosse Bodies senden und den Prozess so in OOM treiben. Eine reine
Content-Length-Pruefung reicht nicht: der Header kann fehlen oder luegen
(Chunked Transfer-Encoding). Deshalb wird hier gestreamt und beim
Ueberschreiten des Limits sofort abgebrochen.
"""
from __future__ import annotations

from fastapi import HTTPException, Request

# Echte Stripe-/Shopify-Webhook-Payloads liegen deutlich unter 1 MiB.
MAX_WEBHOOK_BODY_BYTES = 1_000_000


async def read_bounded_body(request: Request, limit: int = MAX_WEBHOOK_BODY_BYTES) -> bytes:
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > limit:
            raise HTTPException(status_code=413, detail="Body zu gross")
        chunks.append(chunk)
    return b"".join(chunks)
