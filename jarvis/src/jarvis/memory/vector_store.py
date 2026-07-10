"""Vector database abstraction with two backends.

* :class:`ChromaVectorStore` - persistent ChromaDB collection (optional dep).
* :class:`LocalVectorStore` - dependency-free cosine-similarity store
  persisted as JSON; always available as fallback.

Embeddings come from an :class:`Embedder`. The default
:class:`HashingEmbedder` needs no network or model download; when an
embedding-capable provider is configured, :class:`ProviderEmbedder` is used.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jarvis.core.logging import get_logger

logger = get_logger("memory.vector")

_TOKEN_RE = re.compile(r"[\w']+", re.UNICODE)


class Embedder(ABC):
    """Turns texts into vectors."""

    dimension: int = 384

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder(Embedder):
    """Deterministic bag-of-words feature hashing (no model, no network).

    Not semantically as strong as a neural embedding, but robust, fast and
    fully offline - a sound default until a real embedding provider is
    configured.
    """

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = _TOKEN_RE.findall(text.lower())
        for i, token in enumerate(tokens):
            for gram in (token, f"{token}_{tokens[i + 1]}" if i + 1 < len(tokens) else None):
                if gram is None:
                    continue
                digest = hashlib.blake2b(gram.encode("utf-8"), digest_size=8).digest()
                index = int.from_bytes(digest[:4], "little") % self.dimension
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


class ProviderEmbedder(Embedder):
    """Embeds via the model router's configured embedding provider."""

    def __init__(self, router: Any, dimension: int = 1536) -> None:
        self._router = router
        self.dimension = dimension

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = await self._router.embed(texts)
        if vectors:
            self.dimension = len(vectors[0])
        return vectors


@dataclass(slots=True)
class VectorRecord:
    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


class VectorStore(ABC):
    """Minimal vector store contract used by RAG and the memory agent."""

    @abstractmethod
    async def add(self, texts: list[str], metadatas: list[dict[str, Any]] | None = None) -> list[str]: ...

    @abstractmethod
    async def query(self, text: str, top_k: int = 6, where: dict[str, Any] | None = None) -> list[VectorRecord]: ...

    @abstractmethod
    async def delete(self, ids: list[str]) -> None: ...

    @abstractmethod
    async def count(self) -> int: ...


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)


class LocalVectorStore(VectorStore):
    """JSON-persisted store with exact cosine search. Fine for tens of thousands of records."""

    def __init__(self, embedder: Embedder, persist_path: Path | None = None) -> None:
        self._embedder = embedder
        self._path = persist_path
        self._records: dict[str, dict[str, Any]] = {}
        if persist_path is not None and persist_path.is_file():
            try:
                self._records = json.loads(persist_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                logger.warning("Could not load vector store from %s; starting empty", persist_path)

    def _persist(self) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._records, ensure_ascii=False), encoding="utf-8")

    async def add(self, texts: list[str], metadatas: list[dict[str, Any]] | None = None) -> list[str]:
        vectors = await self._embedder.embed(texts)
        ids: list[str] = []
        for i, (text, vector) in enumerate(zip(texts, vectors)):
            record_id = uuid.uuid4().hex
            self._records[record_id] = {
                "text": text,
                "vector": vector,
                "metadata": (metadatas[i] if metadatas else {}) or {},
            }
            ids.append(record_id)
        self._persist()
        return ids

    async def query(
        self, text: str, top_k: int = 6, where: dict[str, Any] | None = None
    ) -> list[VectorRecord]:
        if not self._records:
            return []
        [query_vector] = await self._embedder.embed([text])
        scored: list[VectorRecord] = []
        for record_id, record in self._records.items():
            metadata = record.get("metadata", {})
            if where and any(metadata.get(k) != v for k, v in where.items()):
                continue
            scored.append(
                VectorRecord(
                    id=record_id,
                    text=record["text"],
                    metadata=metadata,
                    score=_cosine(query_vector, record["vector"]),
                )
            )
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]

    async def delete(self, ids: list[str]) -> None:
        for record_id in ids:
            self._records.pop(record_id, None)
        self._persist()

    async def count(self) -> int:
        return len(self._records)


class ChromaVectorStore(VectorStore):
    """ChromaDB-backed store (persistent client). Requires the ``vector`` extra."""

    def __init__(self, embedder: Embedder, persist_dir: Path, collection: str = "jarvis") -> None:
        import chromadb  # local import: optional dependency

        self._embedder = embedder
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection(
            collection, metadata={"hnsw:space": "cosine"}
        )

    async def add(self, texts: list[str], metadatas: list[dict[str, Any]] | None = None) -> list[str]:
        vectors = await self._embedder.embed(texts)
        ids = [uuid.uuid4().hex for _ in texts]
        self._collection.add(
            ids=ids,
            documents=texts,
            embeddings=vectors,
            metadatas=[(m or {"_": "1"}) for m in (metadatas or [{} for _ in texts])],
        )
        return ids

    async def query(
        self, text: str, top_k: int = 6, where: dict[str, Any] | None = None
    ) -> list[VectorRecord]:
        [query_vector] = await self._embedder.embed([text])
        result = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where or None,
        )
        records: list[VectorRecord] = []
        ids = result.get("ids") or [[]]
        documents = result.get("documents") or [[]]
        metadatas = result.get("metadatas") or [[]]
        distances = result.get("distances") or [[]]
        for i, record_id in enumerate(ids[0]):
            distance = distances[0][i] if distances and distances[0] else 1.0
            records.append(
                VectorRecord(
                    id=record_id,
                    text=documents[0][i] if documents and documents[0] else "",
                    metadata=dict(metadatas[0][i]) if metadatas and metadatas[0] else {},
                    score=1.0 - float(distance),
                )
            )
        return records

    async def delete(self, ids: list[str]) -> None:
        if ids:
            self._collection.delete(ids=ids)

    async def count(self) -> int:
        return int(self._collection.count())


def create_vector_store(
    backend: str, embedder: Embedder, data_dir: Path, collection: str
) -> VectorStore:
    """Factory honouring ``memory.vector_backend`` with graceful fallback."""
    if backend in ("auto", "chroma"):
        try:
            return ChromaVectorStore(embedder, data_dir / "memory" / "chroma", collection)
        except ImportError:
            if backend == "chroma":
                raise
            logger.info("chromadb not installed; using local vector store")
    return LocalVectorStore(embedder, data_dir / "memory" / "vectors.json")
