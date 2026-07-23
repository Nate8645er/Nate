"""Ingest-Pipeline: Rohtext → Chunks → (batched) Embeddings → VectorStore.

Jeder Chunk trägt `tenant` + `doc_id` + Metadaten. Embeddings werden in EINEM
Batch je Dokument erzeugt (Durchsatz). Additiv — ersetzt die bestehende
`gedaechtnis`-Tabelle nicht, sondern ergänzt semantisches Retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass

from .chunking import chunk_text
from .embedding import Embedder
from .vectorstore import Document, VectorStore


@dataclass(frozen=True)
class IngestResult:
    doc_id: str
    tenant: str
    chunks: int


class IngestPipeline:
    def __init__(self, store: VectorStore, embedder: Embedder,
                 max_chars: int = 800, overlap: int = 150) -> None:
        self._store = store
        self._embedder = embedder
        self._max_chars = max_chars
        self._overlap = overlap

    def ingest(self, tenant: str, doc_id: str, text: str, metadata: dict | None = None) -> IngestResult:
        if not tenant:
            raise ValueError("ingest verlangt einen tenant")
        chunks = chunk_text(text, self._max_chars, self._overlap)
        if not chunks:
            return IngestResult(doc_id, tenant, 0)
        vectors = self._embedder.embed(chunks)  # batched
        docs = [
            Document(
                id=f"{doc_id}#{i}", tenant=tenant, text=chunk, vector=vec,
                metadata={**(metadata or {}), "doc_id": doc_id, "chunk": i},
            )
            for i, (chunk, vec) in enumerate(zip(chunks, vectors))
        ]
        self._store.upsert(docs)
        return IngestResult(doc_id, tenant, len(docs))
