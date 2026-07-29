"""Retrieval mit Reranking (Auftrag §Phase 3).

Ablauf: Query einbetten → VectorStore-Suche (kandidaten) → Reranking → Top-k.
`Reranker` ist ein Interface; `LexicalReranker` ist ein offline-Standard
(Token-Overlap), der ohne Modell/Netz sinnvoll nachsortiert. Ein Cross-Encoder
kann später hinter demselben Interface eingehängt werden.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .embedding import Embedder, tokenize
from .vectorstore import ScoredDocument, VectorStore


@runtime_checkable
class Reranker(Protocol):
    def rerank(self, query: str, candidates: list[ScoredDocument], k: int) -> list[ScoredDocument]: ...


class NoopReranker:
    def rerank(self, query: str, candidates: list[ScoredDocument], k: int) -> list[ScoredDocument]:
        return candidates[:k]


class LexicalReranker:
    """Mischt Vektor-Score mit lexikalischem Token-Overlap (offline)."""

    def __init__(self, alpha: float = 0.7) -> None:
        # alpha=Gewicht des Vektor-Scores, (1-alpha)=lexikalisch
        self._alpha = alpha

    def rerank(self, query: str, candidates: list[ScoredDocument], k: int) -> list[ScoredDocument]:
        q = set(tokenize(query))
        if not q:
            return candidates[:k]
        rescored: list[ScoredDocument] = []
        for c in candidates:
            doc_tokens = set(tokenize(c.document.text))
            overlap = len(q & doc_tokens) / len(q)
            mixed = self._alpha * c.score + (1 - self._alpha) * overlap
            rescored.append(ScoredDocument(c.document, mixed))
        rescored.sort(key=lambda s: s.score, reverse=True)
        return rescored[:k]


class Retriever:
    def __init__(self, store: VectorStore, embedder: Embedder, reranker: Reranker | None = None) -> None:
        self._store = store
        self._embedder = embedder
        self._reranker = reranker or NoopReranker()

    def retrieve(self, tenant: str, query: str, k: int = 5, candidate_k: int | None = None) -> list[ScoredDocument]:
        cand_k = candidate_k or max(k * 4, k)
        query_vec = self._embedder.embed([query])[0]
        candidates = self._store.search(tenant, query_vec, k=cand_k)
        return self._reranker.rerank(query, candidates, k)
