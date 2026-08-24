"""Retrieval-augmented generation: chunking, indexing and retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jarvis.core.logging import get_logger
from jarvis.memory.vector_store import VectorRecord, VectorStore

logger = get_logger("memory.rag")


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks, preferring paragraph/sentence borders."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    overlap = max(0, min(overlap, chunk_size // 2))
    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # Prefer to break at a paragraph, then sentence, then space.
            for separator in ("\n\n", ". ", "\n", " "):
                cut = text.rfind(separator, start + chunk_size // 2, end)
                if cut != -1:
                    end = cut + len(separator)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


@dataclass(slots=True)
class RagResult:
    """A retrieved context block with provenance."""

    text: str
    source: str
    score: float


class RagPipeline:
    """Indexes documents into the vector store and retrieves cited context."""

    def __init__(
        self,
        store: VectorStore,
        *,
        chunk_size: int = 900,
        chunk_overlap: int = 150,
        top_k: int = 6,
    ) -> None:
        self._store = store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k

    async def index_text(
        self, text: str, *, source: str, metadata: dict[str, Any] | None = None
    ) -> int:
        """Chunk and index a text; returns the number of chunks stored."""
        chunks = chunk_text(text, self.chunk_size, self.chunk_overlap)
        if not chunks:
            return 0
        base = {"source": source, "kind": "document", **(metadata or {})}
        await self._store.add(chunks, [dict(base, chunk=i) for i in range(len(chunks))])
        logger.info("Indexed %d chunks from %s", len(chunks), source)
        return len(chunks)

    async def index_file(self, path: Path, *, metadata: dict[str, Any] | None = None) -> int:
        """Index a UTF-8 readable file (txt/md/code). PDFs go through the desktop office tools."""
        text = path.read_text(encoding="utf-8", errors="replace")
        return await self.index_text(text, source=str(path), metadata=metadata)

    async def retrieve(self, query: str, top_k: int | None = None) -> list[RagResult]:
        records: list[VectorRecord] = await self._store.query(
            query, top_k=top_k or self.top_k, where={"kind": "document"}
        )
        return [
            RagResult(text=r.text, source=str(r.metadata.get("source", "unknown")), score=r.score)
            for r in records
        ]

    async def build_context(self, query: str, top_k: int | None = None) -> str:
        """Format retrieved chunks as a citation-annotated context block."""
        results = await self.retrieve(query, top_k)
        if not results:
            return ""
        blocks = [
            f"[{i + 1}] (source: {result.source})\n{result.text}"
            for i, result in enumerate(results)
        ]
        return (
            "Relevant retrieved context (cite sources as [n] when used):\n\n"
            + "\n\n---\n\n".join(blocks)
        )
