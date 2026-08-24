"""Office document reading and writing: PDF, Excel, Word and PowerPoint.

All heavy libraries (pypdf, openpyxl, python-docx, python-pptx) are imported
lazily, all blocking work runs in a thread, and every path is validated by the
caller-supplied :class:`~jarvis.desktop.files.FileManager` sandbox.
"""

from __future__ import annotations

import asyncio
import importlib
from typing import Any

from jarvis.core.errors import DesktopError
from jarvis.desktop.files import FileManager


def _require(module: str, package: str) -> Any:
    """Import an optional office dependency or fail with an install hint."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise DesktopError(
            f"{package} is not installed. Install it with: "
            "pip install 'jarvis-assistant[desktop]'",
            cause=exc,
        ) from exc


def _parse_pages(pages: str, page_count: int) -> list[int]:
    """Parse a 1-based page spec like ``'1-3,7'`` into 0-based indices."""
    if not pages.strip():
        return list(range(page_count))
    indices: list[int] = []
    try:
        for part in pages.split(","):
            chunk = part.strip()
            if not chunk:
                continue
            if "-" in chunk:
                start_text, _, end_text = chunk.partition("-")
                start, end = int(start_text), int(end_text)
            else:
                start = end = int(chunk)
            indices.extend(range(start - 1, end))
    except ValueError as exc:
        raise DesktopError(f"Invalid page specification '{pages}' (use e.g. '1-3,7')") from exc
    return [i for i in indices if 0 <= i < page_count]


# -- PDF ---------------------------------------------------------------------


async def read_pdf(files: FileManager, path: str, pages: str = "") -> str:
    """Extract text from a PDF; *pages* is an optional 1-based spec like '1-3,7'."""
    pypdf = _require("pypdf", "pypdf")
    target = files.resolve(path)

    def _read() -> str:
        reader = pypdf.PdfReader(str(target))
        indices = _parse_pages(pages, len(reader.pages))
        text = "\n\n".join((reader.pages[i].extract_text() or "") for i in indices)
        return text.strip() or "(no extractable text)"

    return await asyncio.to_thread(_read)


# -- Excel -------------------------------------------------------------------


async def read_excel(files: FileManager, path: str, sheet: str = "") -> list[list[Any]]:
    """Read a worksheet (the active one by default) as a list of rows."""
    openpyxl = _require("openpyxl", "openpyxl")
    target = files.resolve(path)

    def _read() -> list[list[Any]]:
        workbook = openpyxl.load_workbook(str(target), read_only=True, data_only=True)
        try:
            if sheet:
                if sheet not in workbook.sheetnames:
                    raise DesktopError(f"Worksheet '{sheet}' not found in '{target.name}'")
                worksheet = workbook[sheet]
            else:
                worksheet = workbook.active
            return [list(row) for row in worksheet.iter_rows(values_only=True)]
        finally:
            workbook.close()

    return await asyncio.to_thread(_read)


async def write_excel(
    files: FileManager, path: str, rows: list[list[Any]], sheet: str = "Sheet1"
) -> str:
    """Create an .xlsx workbook from a list of rows (list of lists)."""
    openpyxl = _require("openpyxl", "openpyxl")
    target = files.resolve(path)

    def _write() -> str:
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = sheet or "Sheet1"
        for row in rows:
            worksheet.append(list(row))
        target.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(str(target))
        return str(target)

    return await asyncio.to_thread(_write)


# -- Word --------------------------------------------------------------------


async def read_word(files: FileManager, path: str) -> str:
    """Return the paragraph text of a .docx document."""
    docx = _require("docx", "python-docx")
    target = files.resolve(path)

    def _read() -> str:
        document = docx.Document(str(target))
        return "\n".join(p.text for p in document.paragraphs).strip()

    return await asyncio.to_thread(_read)


async def write_word(files: FileManager, path: str, text: str) -> str:
    """Create a .docx document from markdown-ish plain text.

    Lines starting with ``#`` become headings (level = number of ``#``),
    all other non-empty lines become paragraphs.
    """
    docx = _require("docx", "python-docx")
    target = files.resolve(path)

    def _write() -> str:
        document = docx.Document()
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                stripped = line.lstrip("#")
                level = min(len(line) - len(stripped), 9)
                document.add_heading(stripped.strip(), level=level)
            else:
                document.add_paragraph(line)
        target.parent.mkdir(parents=True, exist_ok=True)
        document.save(str(target))
        return str(target)

    return await asyncio.to_thread(_write)


# -- PowerPoint ---------------------------------------------------------------


async def read_powerpoint(files: FileManager, path: str) -> str:
    """Extract all text from a .pptx presentation, slide by slide."""
    pptx = _require("pptx", "python-pptx")
    target = files.resolve(path)

    def _read() -> str:
        presentation = pptx.Presentation(str(target))
        chunks: list[str] = []
        for number, slide in enumerate(presentation.slides, start=1):
            lines = [
                shape.text_frame.text.strip()
                for shape in slide.shapes
                if shape.has_text_frame and shape.text_frame.text.strip()
            ]
            chunks.append(f"--- Slide {number} ---\n" + "\n".join(lines))
        return "\n\n".join(chunks).strip()

    return await asyncio.to_thread(_read)


async def write_powerpoint(files: FileManager, path: str, slides: list[dict[str, Any]]) -> str:
    """Create a .pptx presentation from ``[{"title": ..., "bullets": [...]}]``."""
    pptx = _require("pptx", "python-pptx")
    target = files.resolve(path)

    def _write() -> str:
        presentation = pptx.Presentation()
        layout = presentation.slide_layouts[1]  # "Title and Content"
        for spec in slides:
            slide = presentation.slides.add_slide(layout)
            slide.shapes.title.text = str(spec.get("title", ""))
            bullets = [str(b) for b in spec.get("bullets", [])]
            if bullets:
                body = slide.placeholders[1].text_frame
                body.text = bullets[0]
                for bullet in bullets[1:]:
                    body.add_paragraph().text = bullet
        target.parent.mkdir(parents=True, exist_ok=True)
        presentation.save(str(target))
        return str(target)

    return await asyncio.to_thread(_write)
