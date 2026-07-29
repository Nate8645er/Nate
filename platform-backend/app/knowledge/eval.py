"""RAG-Evaluation — messbare Qualität (Auftrag §Phase 3: 'RAG mit messbarer Qualität').

Kleine, abhängigkeitsfreie Metriken über einen gelabelten Satz aus (Query,
relevante doc_ids). Liefert recall@k und MRR. So wird Retrieval-Qualität eine
Zahl, die über Änderungen hinweg verglichen werden kann.
"""

from __future__ import annotations

from dataclasses import dataclass

from .retrieval import Retriever


@dataclass(frozen=True)
class EvalCase:
    query: str
    relevant_doc_ids: frozenset[str]


@dataclass(frozen=True)
class EvalResult:
    recall_at_k: float
    mrr: float
    k: int
    n: int


def _doc_id_of(chunk_doc_id: str) -> str:
    # Chunk-IDs sind "<doc_id>#<i>" → auf das Dokument zurückführen.
    return chunk_doc_id.rsplit("#", 1)[0]


def evaluate(retriever: Retriever, tenant: str, cases: list[EvalCase], k: int = 5) -> EvalResult:
    if not cases:
        return EvalResult(0.0, 0.0, k, 0)
    recall_sum = 0.0
    rr_sum = 0.0
    for case in cases:
        results = retriever.retrieve(tenant, case.query, k=k)
        found_docs = [_doc_id_of(r.document.id) for r in results]
        hit = any(d in case.relevant_doc_ids for d in found_docs)
        recall_sum += 1.0 if hit else 0.0
        rr = 0.0
        for rank, d in enumerate(found_docs, start=1):
            if d in case.relevant_doc_ids:
                rr = 1.0 / rank
                break
        rr_sum += rr
    n = len(cases)
    return EvalResult(recall_sum / n, rr_sum / n, k, n)
