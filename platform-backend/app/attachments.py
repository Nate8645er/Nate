"""Anhang-Verarbeitung fuer den Chat: Bild-Validierung (Vision-Input) und
Dokument-Text-Extraktion (PDF/Text/Markdown als Kontext-Injection).

SICHERHEITSKRITISCH (Bilder): der Client behauptet einen MIME-Typ im
`data:image/...;base64,...`-URI-Praefix. Dieser Praefix ist reiner Text und
beweist NICHTS ueber die tatsaechlichen Bytes -- ein Client koennte beliebige
Daten mit einem gefaelschten Bild-Praefix schicken. Deshalb werden nach dem
Base64-Decode die ECHTEN Magic-Bytes/Signaturen geprueft (PNG/JPEG/WebP/GIF);
der behauptete Typ dient nur der Fehlermeldung, nie der Entscheidung, was
akzeptiert wird. Dieselbe Grundregel gilt fuer PDFs (Signatur "%PDF-").

DoS-Schutz (analog MAX_CONTENT_CHARS/MAX_MESSAGES in routes/chat.py): ein
Client koennte sonst beliebig grosse Base64-Strings oder Dateien schicken und
Server-Speicher/Gateway-Anfrage aufblaehen -- deshalb harte Groessenlimits
VOR jeder teureren Verarbeitung (Decode/Parsing).
"""
from __future__ import annotations

import base64
import binascii
import io
import re


class AttachmentError(Exception):
    """Eine Anhang-Validierung ist fehlgeschlagen. Vom Aufrufer (routes/chat.py,
    routes/attachments.py) in eine klare HTTP-400-Antwort zu uebersetzen --
    nie stillschweigend ignorieren, nie crashen lassen."""


# --- Bilder (Vision-Input) --------------------------------------------------

# 5 MB nach Base64-Decode, pro Bild -- ein Client koennte sonst beliebig
# grosse Base64-Strings schicken und den Server-Speicher/die Gateway-Anfrage
# aufblaehen (DoS-Risiko).
MAX_IMAGE_BYTES = 5 * 1024 * 1024
# Hoechstens 4 Bilder pro Nachricht -- verhindert, dass eine einzelne
# Nachricht beliebig viele (je bis zu MAX_IMAGE_BYTES grosse) Bilder traegt.
MAX_IMAGES_PER_MESSAGE = 4

# Bekannte Magic-Bytes/Signaturen der unterstuetzten Bildformate. WebP wird
# separat geprueft (RIFF-Container, Signatur nicht an Byte 0 allein erkennbar).
_IMAGE_SIGNATURES: list[tuple[bytes, str]] = [
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpeg"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
]

_MIME_SUBTYPE_ALIASES = {"jpg": "jpeg"}

_DATA_URL_RE = re.compile(r"^data:image/([a-zA-Z0-9.+-]+);base64,(.+)$", re.DOTALL)


def _sniff_image_type(data: bytes) -> str | None:
    """Bestimmt den tatsaechlichen Bildtyp anhand der echten Magic-Bytes --
    NICHT anhand eines vom Client behaupteten Praefix. None, wenn keine der
    unterstuetzten Signaturen (PNG/JPEG/GIF/WebP) passt."""
    for sig, kind in _IMAGE_SIGNATURES:
        if data.startswith(sig):
            return kind
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def validate_image_data_url(data_url: str) -> bytes:
    """Prueft einen `data:image/...;base64,...`-URI vollstaendig (Format,
    Base64-Gueltigkeit, Groessenlimit, echte Bild-Signatur) und gibt die
    dekodierten, verifizierten Bild-Bytes zurueck. Wirft `AttachmentError`
    bei JEDEM Problem -- nie eine andere Exception nach aussen."""
    match = _DATA_URL_RE.match((data_url or "").strip())
    if not match:
        raise AttachmentError(
            "Ungueltiges Bildformat -- erwartet wird ein data:image/...;base64,...-URI"
        )
    declared_subtype_raw, b64_payload = match.groups()
    declared_subtype = _MIME_SUBTYPE_ALIASES.get(
        declared_subtype_raw.lower(), declared_subtype_raw.lower()
    )

    try:
        raw = base64.b64decode(b64_payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AttachmentError("Ungueltige Base64-Bilddaten") from exc

    if not raw:
        raise AttachmentError("Leere Bilddaten")
    if len(raw) > MAX_IMAGE_BYTES:
        raise AttachmentError(
            f"Bild ueberschreitet das Groessenlimit von {MAX_IMAGE_BYTES // (1024 * 1024)} MB"
        )

    sniffed = _sniff_image_type(raw)
    if sniffed is None:
        raise AttachmentError(
            "Die Datei ist kein erkennbares Bild (PNG/JPEG/WebP/GIF) -- die "
            "tatsaechlichen Daten stimmen nicht mit einem Bildformat ueberein"
        )
    if sniffed != declared_subtype:
        raise AttachmentError(
            f"Bildformat stimmt nicht ueberein: angegeben '{declared_subtype}', "
            f"tatsaechliche Daten sind '{sniffed}'"
        )
    return raw


# --- Dokumente (PDF/Text/Markdown als Kontext-Injection) --------------------

# 10 MB Rohdatei, VOR dem Parsen geprueft -- ein Client koennte sonst eine
# riesige Datei hochladen und den Server beim Parsen (v.a. PDF) blockieren.
MAX_DOCUMENT_RAW_BYTES = 10 * 1024 * 1024
# Analog MAX_RESULT_CHARS in web_fetch_tool.py: der extrahierte Text wird auf
# eine sinnvolle Zeichengrenze gekuerzt, bevor er als Kontext-Nachricht in den
# Chat einfliesst.
MAX_DOCUMENT_CHARS = 20_000

_PDF_SIGNATURE = b"%PDF-"


def extract_document_text(filename: str, content_type: str | None, raw: bytes) -> str:
    """Extrahiert lesbaren Text aus einem hochgeladenen Dokument (PDF oder
    Text/Markdown) und kuerzt ihn auf `MAX_DOCUMENT_CHARS` Zeichen. Braucht
    KEIN Vision-Modell -- der extrahierte Text funktioniert mit jedem am
    Gateway registrierten Modell.

    Wirft `AttachmentError` bei zu grosser Rohdatei, kaputtem/gefaelschtem PDF
    oder leerem Upload -- NIE eine andere Exception (ein einzelner kaputter
    Upload darf den Server nicht crashen)."""
    if len(raw) > MAX_DOCUMENT_RAW_BYTES:
        raise AttachmentError(
            f"Datei ueberschreitet das Groessenlimit von "
            f"{MAX_DOCUMENT_RAW_BYTES // (1024 * 1024)} MB"
        )
    if not raw:
        raise AttachmentError("Datei ist leer")

    claims_pdf = (content_type == "application/pdf") or filename.lower().endswith(".pdf")
    is_actually_pdf = raw.startswith(_PDF_SIGNATURE)

    if claims_pdf or is_actually_pdf:
        if not is_actually_pdf:
            # Behauptet PDF (Dateiname/Content-Type), tatsaechliche Bytes
            # aber ohne PDF-Signatur -- nicht vertrauensselig durchreichen.
            raise AttachmentError(
                "Datei gibt sich als PDF aus, die tatsaechlichen Daten sind aber kein PDF"
            )
        text = _extract_pdf_text(raw)
    else:
        text = _extract_plain_text(raw)

    return text[:MAX_DOCUMENT_CHARS]


def _extract_pdf_text(raw: bytes) -> str:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(raw))
        pages_text = [page.extract_text() or "" for page in reader.pages]
    except PdfReadError as exc:
        raise AttachmentError(
            "PDF konnte nicht gelesen werden (beschaedigt oder kein gueltiges PDF)"
        ) from exc
    except Exception as exc:  # noqa: BLE001 -- ein kaputtes PDF darf den Server nie crashen
        raise AttachmentError("PDF konnte nicht gelesen werden") from exc

    text = "\n".join(pages_text).strip()
    if not text:
        raise AttachmentError("PDF enthaelt keinen extrahierbaren Text (z.B. reine Bildscans)")
    return text


def _extract_plain_text(raw: bytes) -> str:
    """Text/Markdown wird direkt dekodiert -- ungueltige UTF-8-Sequenzen
    werden ersetzt statt die ganze Anfrage scheitern zu lassen."""
    return raw.decode("utf-8", errors="replace")


def build_document_context_message(filename: str, text: str) -> dict:
    """Baut die Kontext-Nachricht, die VOR die eigentliche User-Nachricht in
    `messages` eingefuegt wird (role='system', damit das Modell den
    Dokumentinhalt als Hintergrund behandelt, nicht als Nutzer-Anweisung).
    Braucht KEIN Vision-Modell -- funktioniert mit jedem registrierten
    Modell. Aufrufer: das Frontend haengt den von `POST
    /v1/attachments/extract` gelieferten Text ueber diese Funktion als
    zusaetzliche Nachricht an die naechste Chat-Anfrage (siehe README --
    kein persistenter Datei-Storage noetig)."""
    return {
        "role": "system",
        "content": f"Anhang '{filename}':\n\n{text}",
    }
