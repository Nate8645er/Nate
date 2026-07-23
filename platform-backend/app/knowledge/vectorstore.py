"""VectorStore — Interface + In-Memory- und Qdrant-Adapter.

Mandantentrennung ist Pflicht: `search` verlangt IMMER einen `tenant`; ein
Tenant sieht ausschließlich seine eigenen Vektoren. Das ist bewusst schon in
Phase 3 verankert (Risiko #3 aus PHASE-1-PLAN.md), nicht erst in Phase 6.

`InMemoryVectorStore` (dependency-frei, für kleine Tenants/Tests) und
`QdrantVectorStore` (echter Adapter; im Test über den `:memory:`-Modus des
qdrant-clients ohne Server lauffähig) teilen dasselbe Interface.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Document:
    id: str
    tenant: str
    text: str
    vector: list[float]
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ScoredDocument:
    document: Document
    score: float


@runtime_checkable
class VectorStore(Protocol):
    def upsert(self, docs: list[Document]) -> None: ...
    def search(self, tenant: str, query_vector: list[float], k: int = 5) -> list[ScoredDocument]: ...
    def count(self, tenant: str | None = None) -> int: ...


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


class InMemoryVectorStore:
    """Einfacher, exakter Cosine-Store. Für Tests und kleine Tenants."""

    def __init__(self) -> None:
        self._docs: dict[str, Document] = {}

    def upsert(self, docs: list[Document]) -> None:
        for d in docs:
            if not d.tenant:
                raise ValueError("Document ohne tenant ist nicht erlaubt")
            self._docs[d.id] = d

    def search(self, tenant: str, query_vector: list[float], k: int = 5) -> list[ScoredDocument]:
        if not tenant:
            raise ValueError("search verlangt einen tenant (Mandantentrennung)")
        scored = [
            ScoredDocument(d, cosine(query_vector, d.vector))
            for d in self._docs.values()
            if d.tenant == tenant  # Isolation
        ]
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:k]

    def count(self, tenant: str | None = None) -> int:
        if tenant is None:
            return len(self._docs)
        return sum(1 for d in self._docs.values() if d.tenant == tenant)


class QdrantVectorStore:
    """Adapter auf qdrant-client. Mandant als Payload-Feld + Filter erzwungen."""

    def __init__(self, client, collection: str, dim: int) -> None:
        from qdrant_client import models

        self._client = client
        self._collection = collection
        self._models = models
        if not client.collection_exists(collection):
            client.create_collection(
                collection,
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
            )

    def _point_id(self, doc_id: str) -> int:
        # Qdrant-Punkt-IDs sind int/UUID; stabiler Hash aus der String-ID.
        import hashlib

        return int.from_bytes(hashlib.blake2b(doc_id.encode(), digest_size=8).digest(), "big")

    def upsert(self, docs: list[Document]) -> None:
        m = self._models
        points = []
        for d in docs:
            if not d.tenant:
                raise ValueError("Document ohne tenant ist nicht erlaubt")
            points.append(
                m.PointStruct(
                    id=self._point_id(d.id),
                    vector=d.vector,
                    payload={"doc_id": d.id, "tenant": d.tenant, "text": d.text, "metadata": d.metadata},
                )
            )
        if points:
            self._client.upsert(self._collection, points=points)

    def search(self, tenant: str, query_vector: list[float], k: int = 5) -> list[ScoredDocument]:
        if not tenant:
            raise ValueError("search verlangt einen tenant (Mandantentrennung)")
        m = self._models
        res = self._client.query_points(
            self._collection,
            query=query_vector,
            limit=k,
            query_filter=m.Filter(must=[m.FieldCondition(key="tenant", match=m.MatchValue(value=tenant))]),
            with_payload=True,
        )
        out: list[ScoredDocument] = []
        for p in res.points:
            pl = p.payload or {}
            out.append(
                ScoredDocument(
                    Document(id=pl.get("doc_id", str(p.id)), tenant=pl.get("tenant", tenant),
                             text=pl.get("text", ""), vector=[], metadata=pl.get("metadata", {})),
                    float(p.score),
                )
            )
        return out

    def count(self, tenant: str | None = None) -> int:
        m = self._models
        flt = None
        if tenant is not None:
            flt = m.Filter(must=[m.FieldCondition(key="tenant", match=m.MatchValue(value=tenant))])
        return self._client.count(self._collection, count_filter=flt).count
