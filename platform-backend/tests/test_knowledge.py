"""Tests der Wissens-Schicht (RAG) — ohne Netz/GPU."""

import pytest

from app.knowledge.chunking import chunk_text, normalize
from app.knowledge.embedding import HashingEmbedder, tokenize
from app.knowledge.eval import EvalCase, evaluate
from app.knowledge.ingest import IngestPipeline
from app.knowledge.retrieval import LexicalReranker, Retriever
from app.knowledge.vectorstore import (
    Document,
    InMemoryVectorStore,
    QdrantVectorStore,
    cosine,
)


# ---------------- Chunking ----------------
def test_normalize_und_kurzer_text():
    assert normalize("a\r\n  b   c") == "a\n b c"
    assert chunk_text("kurz") == ["kurz"]
    assert chunk_text("") == []


def test_chunking_ueberlappend_und_wortgrenzen():
    text = " ".join(f"wort{i}" for i in range(400))  # weit über 800 Zeichen
    chunks = chunk_text(text, max_chars=200, overlap=40)
    assert len(chunks) > 3
    assert all(len(c) <= 200 for c in chunks)
    assert not any(c.endswith("wor") for c in chunks)  # nie mitten im Wort


def test_chunking_validiert_parameter():
    with pytest.raises(ValueError):
        chunk_text("x", max_chars=100, overlap=100)


# ---------------- Embedding ----------------
def test_hashing_embedder_deterministisch_und_normiert():
    e = HashingEmbedder(dim=64)
    a1, a2 = e.embed(["hallo welt", "hallo welt"])
    assert a1 == a2                              # deterministisch
    norm = sum(x * x for x in a1) ** 0.5
    assert abs(norm - 1.0) < 1e-9                # L2-normiert
    assert e.dim == 64


def test_aehnliche_texte_naeher_als_unaehnliche():
    e = HashingEmbedder(dim=512)
    base, sim, diff = e.embed([
        "die katze sitzt auf der matte",
        "eine katze sitzt auf einer matte",
        "aktienkurse steigen an der boerse",
    ])
    assert cosine(base, sim) > cosine(base, diff)


# ---------------- VectorStore + Tenant-Isolation ----------------
def _corpus():
    e = HashingEmbedder(dim=512)
    docs_a = {
        "a-rechnung": "Wie erstelle ich eine Rechnung mit Mehrwertsteuer und Positionen?",
        "a-offerte": "Eine Offerte fuer eine Badezimmer-Renovation mit Preisuebersicht.",
        "a-mail": "Freundliche Antwort auf eine Kundenbeschwerde ueber eine Verzoegerung.",
    }
    docs_b = {"b-geheim": "Interne Strategie der Firma B, streng vertraulich."}
    return e, docs_a, docs_b


def test_inmemory_tenant_isolation():
    e, docs_a, docs_b = _corpus()
    store = InMemoryVectorStore()
    for i, (did, txt) in enumerate(docs_a.items()):
        store.upsert([Document(did, "tenant-a", txt, e.embed([txt])[0])])
    for did, txt in docs_b.items():
        store.upsert([Document(did, "tenant-b", txt, e.embed([txt])[0])])

    # Tenant A sucht etwas, das nur Tenant B haette -> bekommt NIE B-Dokumente
    q = e.embed(["vertrauliche strategie der firma"])[0]
    res_a = store.search("tenant-a", q, k=5)
    assert all(r.document.tenant == "tenant-a" for r in res_a)
    assert store.count("tenant-b") == 1
    with pytest.raises(ValueError):
        store.search("", q)  # tenant Pflicht


def test_qdrant_adapter_memory_mode():
    qdrant_client = pytest.importorskip("qdrant_client")
    e, docs_a, _ = _corpus()
    client = qdrant_client.QdrantClient(location=":memory:")
    store = QdrantVectorStore(client, collection="test", dim=e.dim)
    for did, txt in docs_a.items():
        store.upsert([Document(did, "tenant-a", txt, e.embed([txt])[0])])
    res = store.search("tenant-a", e.embed(["rechnung mit mehrwertsteuer"])[0], k=2)
    assert res and res[0].document.id == "a-rechnung"
    assert store.count("tenant-a") == 3
    # Fremd-Tenant -> nichts
    assert store.search("tenant-x", e.embed(["rechnung"])[0], k=5) == []


# ---------------- Ingest + Retrieval + Reranking ----------------
def test_ingest_chunkt_und_retrieval_findet():
    e = HashingEmbedder(dim=512)
    store = InMemoryVectorStore()
    pipe = IngestPipeline(store, e, max_chars=120, overlap=20)
    long_text = ("Abschnitt ueber Rechnungen und Mehrwertsteuer. " * 5
                 + "Abschnitt ueber Marketing und Social Media Kampagnen. " * 5)
    res = pipe.ingest("t1", "doc1", long_text)
    assert res.chunks >= 2
    retr = Retriever(store, e, LexicalReranker())
    hits = retr.retrieve("t1", "mehrwertsteuer rechnung", k=1)
    assert hits and "rechnung" in hits[0].document.text.lower()


# ---------------- Evaluation (messbare Qualitaet) ----------------
def test_evaluation_liefert_kennzahlen():
    e, docs_a, _ = _corpus()
    store = InMemoryVectorStore()
    pipe = IngestPipeline(store, e, max_chars=400, overlap=50)
    for did, txt in docs_a.items():
        pipe.ingest("t1", did, txt)
    retr = Retriever(store, e, LexicalReranker())
    cases = [
        EvalCase("rechnung mehrwertsteuer positionen", frozenset({"a-rechnung"})),
        EvalCase("offerte badezimmer renovation preis", frozenset({"a-offerte"})),
        EvalCase("antwort kundenbeschwerde verzoegerung", frozenset({"a-mail"})),
    ]
    result = evaluate(retr, "t1", cases, k=3)
    assert result.n == 3
    assert result.recall_at_k == 1.0    # alle drei im Top-3 gefunden
    assert result.mrr > 0.6
