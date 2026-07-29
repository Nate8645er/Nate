"""Embeddings — Interface + offline-fähige Standard-Implementierung.

`Embedder.embed` ist bewusst **batch-orientiert** (Auftrag §Phase 3: batched
Embeddings sind der dominante Durchsatzhebel).

`HashingEmbedder` erzeugt deterministische Vektoren aus gehashten Tokens —
ohne Modell, ohne Netz, ohne GPU. Er ist kein semantisches Modell, sondern
ein ehrlicher lexikalischer Standard/Fallback (und macht Tests reproduzierbar).
Für echte Semantik wird später ein Modell-Embedder (LiteLLM/lokaler Endpoint)
hinter demselben Interface eingehängt.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol, runtime_checkable

_TOKEN = re.compile(r"[a-zA-ZäöüÄÖÜß0-9]+")


@runtime_checkable
class Embedder(Protocol):
    @property
    def dim(self) -> int: ...
    def embed(self, texts: list[str]) -> list[list[float]]: ...


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text)]


class HashingEmbedder:
    """Bag-of-hashed-tokens → L2-normalisierter Vektor. Deterministisch, offline."""

    def __init__(self, dim: int = 256) -> None:
        if dim <= 0:
            raise ValueError("dim muss > 0 sein")
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def _one(self, text: str) -> list[float]:
        # Unsigned Feature-Hashing (Term-Frequenz): für jedes Token immer eine
        # nicht-negative Komponente → der Vektor ist für nicht-leeren Text nie
        # der Nullvektor (robust auch bei kleiner Dimension). Kollisionen mischen
        # Merkmale, verfälschen die Cosine-Ähnlichkeit aber nicht systematisch.
        vec = [0.0] * self._dim
        for tok in tokenize(text):
            h = hashlib.blake2b(tok.encode("utf-8"), digest_size=8).digest()
            idx = int.from_bytes(h[:4], "big") % self._dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec  # nur bei leerem Text
        return [v / norm for v in vec]

    def embed(self, texts: list[str]) -> list[list[float]]:
        # Batch-Signatur ist der Vertrag; echte Modelle nutzen hier echtes Batching.
        return [self._one(t) for t in texts]
