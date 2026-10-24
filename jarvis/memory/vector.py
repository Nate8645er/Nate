"""Vector memory (semantic search).

Uses ChromaDB or Qdrant when installed/running; otherwise falls back to a
dependency-free naive store (hashed bag-of-words embeddings + cosine
similarity) so JARVIS always has working semantic recall out of the box.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
import uuid
from typing import Any, Protocol

log = logging.getLogger(__name__)

_DIM = 512


def _embed(text: str) -> list[float]:
    """Deterministic hashed bag-of-words embedding (fallback backend)."""
    vec = [0.0] * _DIM
    for token in re.findall(r"\w+", text.lower()):
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        vec[h % _DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class VectorStore(Protocol):
    async def add(self, text: str, meta: dict[str, Any] | None = None) -> str: ...
    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]: ...


class NaiveVectorStore:
    """In-memory fallback; good enough for personal-scale recall."""

    backend = "naive"

    def __init__(self) -> None:
        self._items: dict[str, tuple[str, dict[str, Any], list[float]]] = {}

    async def add(self, text: str, meta: dict[str, Any] | None = None) -> str:
        doc_id = uuid.uuid4().hex
        self._items[doc_id] = (text, meta or {}, _embed(text))
        return doc_id

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        q = _embed(query)
        scored = [
            {"id": doc_id, "text": text, "meta": meta, "score": _cosine(q, vec)}
            for doc_id, (text, meta, vec) in self._items.items()
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return [s for s in scored[:limit] if s["score"] > 0]


class ChromaVectorStore:
    backend = "chroma"

    def __init__(self, persist_dir: str) -> None:
        import chromadb  # optional dependency

        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection("jarvis_memory")

    async def add(self, text: str, meta: dict[str, Any] | None = None) -> str:
        doc_id = uuid.uuid4().hex
        self._collection.add(ids=[doc_id], documents=[text], metadatas=[meta or {"_": "x"}])
        return doc_id

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        res = self._collection.query(query_texts=[query], n_results=limit)
        out = []
        for i, doc_id in enumerate(res["ids"][0]):
            out.append(
                {
                    "id": doc_id,
                    "text": res["documents"][0][i],
                    "meta": (res["metadatas"][0][i] or {}),
                    "score": 1.0 - (res["distances"][0][i] if res.get("distances") else 0.0),
                }
            )
        return out


def create_vector_store(backend: str, persist_dir: str) -> VectorStore:
    """Pick the best available backend; never fail the boot because of it."""
    if backend in ("auto", "chroma"):
        try:
            store = ChromaVectorStore(persist_dir)
            log.info("Vector memory: ChromaDB at %s", persist_dir)
            return store
        except Exception as exc:  # noqa: BLE001 - optional dependency
            if backend == "chroma":
                log.warning("ChromaDB requested but unavailable (%s); using naive store", exc)
    if backend not in ("auto", "chroma", "naive"):
        log.warning("Unknown vector backend %r; using naive store", backend)
    log.info("Vector memory: naive in-memory store")
    return NaiveVectorStore()
