"""Unit-Tests fuer app/attachments.py -- ohne DB. Deckt die Kernstuecke ab:
Bild-Validierung (Base64, Groessenlimit, ECHTE Magic-Byte-Signatur statt des
blossen behaupteten MIME-Praefixes) und Dokument-Text-Extraktion
(PDF/Text/Markdown, Groessenlimit VOR dem Parsen, Kuerzung)."""
from __future__ import annotations

import base64
import io

import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject

from app.attachments import (
    MAX_DOCUMENT_CHARS,
    MAX_DOCUMENT_RAW_BYTES,
    MAX_IMAGE_BYTES,
    AttachmentError,
    build_document_context_message,
    extract_document_text,
    validate_image_data_url,
)

# Kleinstmoegliches gueltiges PNG (1x1 Pixel, transparent) -- echte
# PNG-Magic-Bytes, kein konstruierter Text.
TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def _build_test_pdf(text: str) -> bytes:
    """Baut ein minimales, aber ECHTES, syntaktisch gueltiges PDF mit genau
    diesem Textinhalt (per pypdf selbst -- keine zusaetzliche Test-Only-
    Abhaengigkeit noetig)."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)

    font_dict = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    font_ref = writer._add_object(font_dict)
    resources = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})
    })
    page[NameObject("/Resources")] = resources

    from pypdf.generic import DecodedStreamObject

    stream_obj = DecodedStreamObject()
    stream_obj.set_data(f"BT /F1 24 Tf 10 100 Td ({text}) Tj ET".encode())
    content_ref = writer._add_object(stream_obj)
    page[NameObject("/Contents")] = content_ref

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# --- Bilder ------------------------------------------------------------


def test_valid_png_data_url_is_accepted():
    data_url = f"data:image/png;base64,{TINY_PNG_B64}"
    raw = validate_image_data_url(data_url)
    assert raw.startswith(b"\x89PNG\r\n\x1a\n")


def test_invalid_format_without_data_prefix_is_rejected():
    with pytest.raises(AttachmentError):
        validate_image_data_url(f"base64,{TINY_PNG_B64}")


def test_invalid_base64_is_rejected_not_crashed():
    with pytest.raises(AttachmentError):
        validate_image_data_url("data:image/png;base64,dies-ist-kein-gueltiges-base64!!!")


def test_empty_base64_payload_is_rejected():
    with pytest.raises(AttachmentError):
        validate_image_data_url("data:image/png;base64,")


def test_oversized_image_is_rejected():
    # Echte PNG-Signatur am Anfang, aber danach so viel Fuellmaterial, dass
    # die dekodierte Groesse das 5-MB-Limit ueberschreitet -- die
    # Groessenpruefung muss VOR/unabhaengig von einer vollstaendigen
    # Bild-Validitaetspruefung greifen.
    raw = b"\x89PNG\r\n\x1a\n" + b"\x00" * (MAX_IMAGE_BYTES + 1)
    data_url = "data:image/png;base64," + base64.b64encode(raw).decode()
    with pytest.raises(AttachmentError, match="Groessenlimit"):
        validate_image_data_url(data_url)


def test_fake_mime_signature_is_rejected():
    """Text-Bytes mit einem behaupteten data:image/png-Praefix -- die echten
    Magic-Bytes stimmen nicht, muss abgelehnt werden statt durchgereicht."""
    raw = b"Das hier ist einfach nur Text, kein Bild."
    data_url = "data:image/png;base64," + base64.b64encode(raw).decode()
    with pytest.raises(AttachmentError, match="kein erkennbares Bild"):
        validate_image_data_url(data_url)


def test_mismatched_declared_type_is_rejected():
    """Echte PNG-Bytes, aber als jpeg deklariert -- der behauptete Typ darf
    nicht einfach uebernommen werden."""
    data_url = f"data:image/jpeg;base64,{TINY_PNG_B64}"
    with pytest.raises(AttachmentError, match="stimmt nicht ueberein"):
        validate_image_data_url(data_url)


def test_jpg_alias_is_normalized_to_jpeg():
    """'jpg' und 'jpeg' sind dasselbe Format -- kein falscher Mismatch."""
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 20
    data_url = "data:image/jpg;base64," + base64.b64encode(jpeg_bytes).decode()
    raw = validate_image_data_url(data_url)
    assert raw.startswith(b"\xff\xd8\xff")


def test_webp_signature_is_recognized():
    webp_bytes = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 20
    data_url = "data:image/webp;base64," + base64.b64encode(webp_bytes).decode()
    raw = validate_image_data_url(data_url)
    assert raw.startswith(b"RIFF")


# --- Dokumente -----------------------------------------------------------


def test_extract_plain_text():
    raw = "Hallo, das ist ein Testdokument.".encode("utf-8")
    text = extract_document_text("notiz.txt", "text/plain", raw)
    assert text == "Hallo, das ist ein Testdokument."


def test_extract_markdown_text():
    raw = "# Titel\n\nEin Absatz mit **Markdown**.".encode("utf-8")
    text = extract_document_text("readme.md", "text/markdown", raw)
    assert "Titel" in text and "Markdown" in text


def test_extract_pdf_text():
    raw = _build_test_pdf("Hallo aus dem Test-PDF")
    text = extract_document_text("dokument.pdf", "application/pdf", raw)
    assert "Hallo aus dem Test-PDF" in text


def test_extract_pdf_text_detected_by_signature_without_pdf_extension():
    """Auch ohne '.pdf'-Endung/Content-Type wird ein echtes PDF an der
    Signatur erkannt und korrekt geparst."""
    raw = _build_test_pdf("Erkannt per Signatur")
    text = extract_document_text("upload", None, raw)
    assert "Erkannt per Signatur" in text


def test_corrupted_pdf_is_rejected_not_crashed():
    raw = b"%PDF-1.4\nkaputter Inhalt, kein gueltiges PDF-Objektmodell"
    with pytest.raises(AttachmentError):
        extract_document_text("kaputt.pdf", "application/pdf", raw)


def test_spoofed_pdf_extension_without_pdf_signature_is_rejected():
    """Dateiname/Content-Type behaupten PDF, die echten Bytes sind aber
    keins -- muss abgelehnt werden, nicht als Text durchgereicht."""
    raw = b"Das ist eigentlich nur Klartext."
    with pytest.raises(AttachmentError, match="kein PDF"):
        extract_document_text("bericht.pdf", "application/pdf", raw)


def test_oversized_raw_document_is_rejected_before_parsing():
    raw = b"a" * (MAX_DOCUMENT_RAW_BYTES + 1)
    with pytest.raises(AttachmentError, match="Groessenlimit"):
        extract_document_text("gross.txt", "text/plain", raw)


def test_empty_document_is_rejected():
    with pytest.raises(AttachmentError):
        extract_document_text("leer.txt", "text/plain", b"")


def test_document_text_is_truncated_to_max_chars():
    raw = ("x" * (MAX_DOCUMENT_CHARS + 5000)).encode("utf-8")
    text = extract_document_text("lang.txt", "text/plain", raw)
    assert len(text) == MAX_DOCUMENT_CHARS


def test_build_document_context_message_format():
    msg = build_document_context_message("bericht.pdf", "Inhalt des Berichts")
    assert msg["role"] == "system"
    assert "bericht.pdf" in msg["content"]
    assert "Inhalt des Berichts" in msg["content"]
