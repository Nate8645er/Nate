"""Dokument-Anhaenge: POST /v1/attachments/extract nimmt eine hochgeladene
Datei (PDF/Text/Markdown) per multipart/form-data entgegen und gibt den
extrahierten, gekuerzten Text direkt zurueck -- KEIN persistenter
Datei-Storage (die Datei existiert nur fuer die Dauer dieser einen Anfrage im
Speicher, es gibt nichts aufzuraeumen).

Endpunkt-Design-Entscheidung (siehe README): fuer BILDER reicht der direkte
JSON-Weg in POST /v1/chat (einfach, kein Storage-Management, ein Bild ist eh
nur fuer die eine Anfrage relevant -- siehe routes/chat.py). Fuer DOKUMENTE
ist dieser separate Extract-Endpunkt sauberer: PDFs/Textdateien koennen
deutlich groesser sein als ein einzelnes Chat-Bild, und nur der (kurze,
gekuerzte) extrahierte TEXT soll in den Chat-Kontext einfliessen, nicht die
Rohdatei -- ein Roundtrip zum Extrahieren, danach haengt das Frontend den
zurueckgegebenen Text als zusaetzliche Kontext-Nachricht an die naechste
POST /v1/chat-Anfrage (siehe attachments.py::build_document_context_message).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..attachments import MAX_DOCUMENT_RAW_BYTES, AttachmentError, extract_document_text
from ..auth import Principal, require_principal
from ..http_limits import read_bounded_upload

router = APIRouter()


@router.post("/v1/attachments/extract")
async def extract_attachment(
    file: UploadFile = File(...),
    principal: Principal = Depends(require_principal),
):
    # Gestreamt gelesen und VOR dem Parsen auf MAX_DOCUMENT_RAW_BYTES
    # begrenzt -- ein Client koennte sonst eine riesige Datei hochladen und
    # den Server beim (potenziell teuren) PDF-Parsing ausbremsen.
    raw = await read_bounded_upload(file, MAX_DOCUMENT_RAW_BYTES)
    try:
        text = extract_document_text(file.filename or "upload", file.content_type, raw)
    except AttachmentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"filename": file.filename, "text": text}
