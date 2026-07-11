"""Optical character recognition via Tesseract (``pytesseract``).

Dependencies are imported lazily; missing Python packages and a missing
Tesseract binary both surface as :class:`~jarvis.core.errors.VisionError`
with actionable install hints.
"""

from __future__ import annotations

import io

from jarvis.core.errors import VisionError
from jarvis.core.logging import get_logger

logger = get_logger("vision.ocr")

_INSTALL_HINT = "Install the vision extras: pip install 'jarvis-assistant[vision]'"


def extract_text(png_bytes: bytes, languages: str = "eng") -> str:
    """Extract text from a PNG image.

    ``languages`` uses Tesseract's ``lang`` syntax, e.g. ``"eng"`` or
    ``"eng+deu"``. Returns the recognised text stripped of surrounding
    whitespace (possibly empty).
    """
    try:
        import pytesseract
    except ImportError as exc:
        raise VisionError(
            f"OCR needs the 'pytesseract' package. {_INSTALL_HINT} "
            "(or: pip install pytesseract).",
            cause=exc,
        ) from exc
    try:
        from PIL import Image
    except ImportError as exc:
        raise VisionError(
            f"OCR needs the 'Pillow' package. {_INSTALL_HINT} (or: pip install Pillow).",
            cause=exc,
        ) from exc

    try:
        with Image.open(io.BytesIO(png_bytes)) as image:
            text = pytesseract.image_to_string(image, lang=languages)
    except pytesseract.TesseractNotFoundError as exc:
        raise VisionError(
            "The Tesseract OCR engine is not installed or not on PATH. "
            "Install it with your package manager, e.g. "
            "'sudo apt install tesseract-ocr' (Debian/Ubuntu), "
            "'brew install tesseract' (macOS), or the Windows installer from "
            "https://github.com/UB-Mannheim/tesseract.",
            cause=exc,
        ) from exc
    except VisionError:
        raise
    except Exception as exc:
        raise VisionError(f"OCR failed: {exc}", cause=exc) from exc
    return text.strip()
