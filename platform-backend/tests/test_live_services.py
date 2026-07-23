"""Live-Integrationstests gegen ECHTE Dienste (Postgres, Qdrant, Redis).

Diese Tests beweisen, dass die Adapter nicht nur gegen In-Memory-/`:memory:`-
Attrappen, sondern gegen laufende Server funktionieren. Sie sind **opt-in**:
Ist ein Dienst nicht erreichbar, wird der Test übersprungen (nicht rot). Damit
bleibt die Standard-Suite offline- und CI-tauglich (Auftrag: „ohne Netz").

Start der Dienste (Entwicklung):
    docker run -d -p 5433:5432 -e POSTGRES_PASSWORD=devpass -e POSTGRES_DB=platform postgres:16-alpine
    docker run -d -p 6333:6333 qdrant/qdrant:latest
    docker run -d -p 6380:6379 redis:7-alpine

Adressen sind über Env überschreibbar (PF_PG_DSN, PF_QDRANT_URL, PF_REDIS_URL).
"""

from __future__ import annotations

import os
import socket

import pytest

from app.knowledge.embedding import HashingEmbedder
from app.knowledge.vectorstore import Document, QdrantVectorStore
from app.models.router import DataClass, ModelRequest, ModelRouter, RoutingContext

PG_DSN = os.environ.get("PF_PG_DSN", "postgresql://postgres:devpass@127.0.0.1:5433/platform")
QDRANT_URL = os.environ.get("PF_QDRANT_URL", "http://127.0.0.1:6333")
REDIS_URL = os.environ.get("PF_REDIS_URL", "redis://127.0.0.1:6380/0")
OLLAMA_URL = os.environ.get("PF_OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("PF_OLLAMA_MODEL", "qwen2.5:0.5b")


def _port_open(host: str, port: int, timeout: float = 0.75) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _skip_unless(host: str, port: int, name: str) -> None:
    if not _port_open(host, port):
        pytest.skip(f"{name} nicht erreichbar auf {host}:{port} — Live-Test übersprungen")


# --------------------------------------------------------------------------- #
# Qdrant — echter Server, Mandantentrennung im Retrieval
# --------------------------------------------------------------------------- #
def test_qdrant_real_server_tenant_isolation() -> None:
    _skip_unless("127.0.0.1", 6333, "Qdrant")
    from qdrant_client import QdrantClient

    client = QdrantClient(url=QDRANT_URL)
    emb = HashingEmbedder(dim=64)
    coll = "pf_live_test"
    # Frische Collection je Lauf (idempotent).
    if client.collection_exists(coll):
        client.delete_collection(coll)
    store = QdrantVectorStore(client, collection=coll, dim=64)

    def vec(text: str) -> list[float]:
        return emb.embed([text])[0]

    store.upsert([
        Document(id="a1", tenant="acme", text="Rechnung bezahlen Frist", vector=vec("Rechnung bezahlen Frist")),
        Document(id="a2", tenant="acme", text="Urlaubsantrag stellen", vector=vec("Urlaubsantrag stellen")),
        Document(id="b1", tenant="globex", text="Rechnung bezahlen Frist", vector=vec("Rechnung bezahlen Frist")),
    ])

    # Tenant acme sucht — darf NIE globex' Dokument sehen.
    hits = store.search("acme", vec("Rechnung Frist"), k=5)
    ids = {h.document.id for h in hits}
    assert "b1" not in ids, "Mandantentrennung verletzt: fremdes Dokument im Ergebnis"
    assert "a1" in ids
    assert store.count("acme") == 2
    assert store.count("globex") == 1

    client.delete_collection(coll)


# --------------------------------------------------------------------------- #
# Postgres — echte Row-Level-Security blockt Cross-Tenant auf DB-Ebene
# --------------------------------------------------------------------------- #
def test_postgres_real_rls_blocks_cross_tenant() -> None:
    _skip_unless("127.0.0.1", 5433, "Postgres")
    import uuid

    import psycopg

    # RLS gilt NICHT für Superuser/BYPASSRLS-Rollen. In Produktion greift die
    # App-Verbindung als *unprivilegierte* Rolle darauf zu — genau das bilden
    # wir hier nach: eigene Rolle ohne BYPASSRLS.
    schema = "rls_" + uuid.uuid4().hex[:8]
    role = "app_" + uuid.uuid4().hex[:8]
    admin = psycopg.connect(PG_DSN, autocommit=True)
    try:
        with admin.cursor() as cur:
            cur.execute(f"CREATE ROLE {role} LOGIN PASSWORD 'x' NOBYPASSRLS")
            cur.execute(f"CREATE SCHEMA {schema} AUTHORIZATION {role}")
            cur.execute(f"SET search_path TO {schema}")
            cur.execute(
                "CREATE TABLE tenant_records ("
                "id text PRIMARY KEY, tenant_id text NOT NULL, kind text, data jsonb)"
            )
            cur.execute("ALTER TABLE tenant_records ENABLE ROW LEVEL SECURITY")
            cur.execute("ALTER TABLE tenant_records FORCE ROW LEVEL SECURITY")
            cur.execute(
                "CREATE POLICY tenant_isolation ON tenant_records "
                "USING (tenant_id = current_setting('app.current_tenant', true)) "
                "WITH CHECK (tenant_id = current_setting('app.current_tenant', true))"
            )
            cur.execute(f"GRANT ALL ON tenant_records TO {role}")
            cur.execute(f"GRANT USAGE ON SCHEMA {schema} TO {role}")

        # Als App-Rolle verbinden (RLS aktiv).
        app_dsn = PG_DSN.rsplit("@", 1)[-1]
        app = psycopg.connect(f"postgresql://{role}:x@{app_dsn}", autocommit=True)
        try:
            with app.cursor() as cur:
                cur.execute(f"SET search_path TO {schema}")
                # Als Tenant acme schreiben.
                cur.execute("SELECT set_config('app.current_tenant', 'acme', false)")
                cur.execute("INSERT INTO tenant_records VALUES ('r1', 'acme', 'note', '{}')")
                # Für globex zu schreiben muss die WITH-CHECK-Policy verletzen.
                with pytest.raises(psycopg.errors.Error):
                    cur.execute("INSERT INTO tenant_records VALUES ('r2', 'globex', 'note', '{}')")

            # Neue Session als Tenant globex — darf acme's Zeile NICHT sehen.
            with app.cursor() as cur:
                cur.execute(f"SET search_path TO {schema}")
                cur.execute("SELECT set_config('app.current_tenant', 'globex', false)")
                cur.execute("SELECT count(*) FROM tenant_records")
                assert cur.fetchone()[0] == 0, "RLS-Leck: globex sieht fremde Zeilen"
                # Als acme sichtbar:
                cur.execute("SELECT set_config('app.current_tenant', 'acme', false)")
                cur.execute("SELECT count(*) FROM tenant_records")
                assert cur.fetchone()[0] == 1
        finally:
            app.close()
    finally:
        with admin.cursor() as cur:
            cur.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
            cur.execute(f"DROP ROLE IF EXISTS {role}")
        admin.close()


# --------------------------------------------------------------------------- #
# Redis — echter Server, atomare Zähler (Basis für Quota/Rate-Limit)
# --------------------------------------------------------------------------- #
def test_redis_real_atomic_counter() -> None:
    _skip_unless("127.0.0.1", 6380, "Redis")
    import redis

    r = redis.Redis.from_url(REDIS_URL)
    key = "pf:live:quota:acme:2026-07-23"
    r.delete(key)
    total = 0
    for _ in range(5):
        total = r.incrby(key, 100)
    assert total == 500
    r.expire(key, 60)
    assert r.ttl(key) > 0
    r.delete(key)


# --------------------------------------------------------------------------- #
# Ollama — ECHTE lokale Inferenz durch den ModelRouter → LiteLLM → Ollama
# --------------------------------------------------------------------------- #
def test_ollama_real_local_inference_through_router() -> None:
    _skip_unless("127.0.0.1", 11434, "Ollama")
    pytest.importorskip("litellm")

    # local_only: Daten dürfen die Umgebung NICHT verlassen → Router muss lokal
    # platzieren und LiteLLM gegen den echten Ollama-Server ausführen.
    ctx = RoutingContext(local_available=True, cloud_available=True)
    router = ModelRouter(ctx, local_base_url=f"{OLLAMA_URL}/v1")

    req = ModelRequest(prompt_tokens_est=20, data_class=DataClass.LOCAL_ONLY, model=OLLAMA_MODEL)
    decision = router.route(req)
    assert decision.placement == "local", "local_only muss lokal platzieren"

    result = router.complete(
        req,
        messages=[{"role": "user", "content": "Sag kurz hallo."}],
    )
    # Bewiesen wird die PIPELINE (Routing → LiteLLM → echter Ollama-Server →
    # Antwort), nicht die Genauigkeit des 0.5B-Modells. Daher: echte, nicht
    # leere Antwort mit realer Token-Nutzung vom lokalen Backend.
    assert result["ok"], f"Lokale Inferenz fehlgeschlagen: {result.get('error')}"
    resp = result["response"]
    text = resp.choices[0].message.content
    assert isinstance(text, str) and text.strip(), "Leere Antwort vom lokalen Modell"
    assert resp.usage.completion_tokens > 0, "Keine Token vom lokalen Backend generiert"
    assert resp.model and OLLAMA_MODEL.split(":")[0] in resp.model
