"""knowledge/ — RAG, Retrieval, Memory (Phase 3, implementiert).

- chunking.py    : Text → überlappende Chunks (rein)
- embedding.py   : Embedder-Interface + offline HashingEmbedder (batched)
- vectorstore.py : VectorStore-Interface + InMemory- und Qdrant-Adapter
                   (Mandantentrennung im search erzwungen)
- retrieval.py   : Retriever + Reranker (LexicalReranker offline)
- ingest.py      : Ingest-Pipeline (Chunk → batched Embed → upsert)
- eval.py        : recall@k / MRR — messbare Retrieval-Qualität

Additiv zur bestehenden `gedaechtnis`-Tabelle; ersetzt sie nicht.
"""
