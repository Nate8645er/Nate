"""Beweist POST /v1/attachments/extract gegen eine echte Postgres-DB (Auth
ueber das Session-Cookie wie jeder andere Endpunkt). Die eigentliche
Extraktions-/Validierungslogik selbst ist bereits in tests/test_attachments.py
erschoepfend getestet -- hier geht es um die HTTP-Schicht: Auth-Pflicht,
multipart-Upload, Body-Groessenlimit VOR dem Parsen, 400 bei kaputten
Dateien."""
from __future__ import annotations

import io
import os

import pytest
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from pypdf import PdfWriter

from app.attachments import MAX_DOCUMENT_RAW_BYTES

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


def _build_test_pdf(text: str) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    font_dict = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    font_ref = writer._add_object(font_dict)
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})
    })
    stream_obj = DecodedStreamObject()
    stream_obj.set_data(f"BT /F1 24 Tf 10 100 Td ({text}) Tj ET".encode())
    page[NameObject("/Contents")] = writer._add_object(stream_obj)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_extract_text_file(client, prov):
    prov("pro")
    r = client.post(
        "/v1/attachments/extract",
        files={"file": ("notiz.txt", b"Wichtiger Kontext aus einer Textdatei.", "text/plain")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["filename"] == "notiz.txt"
    assert body["text"] == "Wichtiger Kontext aus einer Textdatei."


def test_extract_pdf_file(client, prov):
    prov("pro")
    pdf_bytes = _build_test_pdf("Extrahierter PDF Text")
    r = client.post(
        "/v1/attachments/extract",
        files={"file": ("dokument.pdf", pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 200, r.text
    assert "Extrahierter PDF Text" in r.json()["text"]


def test_extract_requires_authentication(client):
    r = client.post(
        "/v1/attachments/extract",
        files={"file": ("notiz.txt", b"Hallo", "text/plain")},
    )
    assert r.status_code == 401


def test_oversized_file_rejected_before_parsing(client, prov):
    prov("pro")
    huge = b"a" * (MAX_DOCUMENT_RAW_BYTES + 1)
    r = client.post(
        "/v1/attachments/extract",
        files={"file": ("gross.txt", huge, "text/plain")},
    )
    assert r.status_code == 400, r.text


def test_corrupted_pdf_rejected_with_400_not_500(client, prov):
    prov("pro")
    r = client.post(
        "/v1/attachments/extract",
        files={"file": ("kaputt.pdf", b"%PDF-1.4\nnicht wirklich ein gueltiges PDF", "application/pdf")},
    )
    assert r.status_code == 400, r.text
