"""Text-Chunking — rein und testbar (Auftrag §Phase 3).

Zerlegt Text in überlappende Stücke an Wort-/Absatzgrenzen. Kein Modell, kein
Netz. Overlap erhält Kontext über Chunk-Grenzen (bessere Retrieval-Qualität).
"""

from __future__ import annotations

import re


def normalize(text: str) -> str:
    """Whitespace vereinheitlichen, Ränder trimmen."""
    return re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n")).strip()


def chunk_text(text: str, max_chars: int = 800, overlap: int = 150) -> list[str]:
    """Teilt `text` in Stücke ≤ `max_chars` mit `overlap` Zeichen Überlappung.

    Bricht bevorzugt an Absatz- dann Wortgrenzen, nie mitten im Wort.
    """
    if max_chars <= 0:
        raise ValueError("max_chars muss > 0 sein")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap muss in [0, max_chars) liegen")

    text = normalize(text)
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        if end < n:
            # an letzter Wort-/Absatzgrenze im Fenster brechen
            window = text[start:end]
            brk = max(window.rfind("\n"), window.rfind(" "))
            if brk > overlap:  # nur brechen, wenn sinnvoll weit vorne
                end = start + brk
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks
