"""PII-Bereinigung für Trainingsdaten (Agent 6 — Sicherheit).

Entfernt vor dem Export personenbezogene/geheime Daten aus Texten:
E-Mails, Telefonnummern, Kreditkarten, IP-Adressen und API-Keys. Die
Bereinigung ist bewusst konservativ (lieber zu viel maskieren) und wird auf
JEDEN exportierten Text angewandt. Sie ist KEINE Garantie, alles zu fangen —
das steht ehrlich in der Doku.
"""

from __future__ import annotations

import re

_PATTERNS = [
    (re.compile(r"\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    (re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{16,}\b"), "[API_KEY]"),
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{10,}\b"), "[API_KEY]"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[CARD]"),          # Kreditkarte
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP]"),
    (re.compile(r"(?<!\d)(?:\+?\d[\d ()/-]{7,}\d)(?!\d)"), "[PHONE]"),
]


def scrub(text: str) -> str:
    """Maskiert PII/Secrets in einem Text."""
    if not text:
        return text
    out = text
    for pat, repl in _PATTERNS:
        out = pat.sub(repl, out)
    return out


def contains_pii(text: str) -> bool:
    return any(pat.search(text or "") for pat, _ in _PATTERNS)
