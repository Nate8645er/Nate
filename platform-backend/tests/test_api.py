"""Tests: HTTP-API v1 (Auth-Kette, Routing-Policy, mandantengetrennte Suche).

Nutzt einen selbst signierten RS256-Schlüssel als injizierten Verifier — kein
laufender Keycloak nötig. Beweist die volle Kette Bearer → Verify → RBAC →
Handler über echte ASGI-Requests (TestClient).
"""

import json
import time

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm

from app.api import deps, v1
from app.knowledge.vectorstore import Document, InMemoryVectorStore
from app.main import app
from app.platform.auth import KeycloakVerifier, OidcConfig

ISSUER = "https://auth.example.com/realms/kunden"
KID = "test-key-1"
client = TestClient(app)


def _keypair_and_jwks():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    pub.update({"kid": KID, "alg": "RS256", "use": "sig"})
    return key, {"keys": [pub]}


def _token(key, roles, tenant="kunden"):
    now = int(time.time())
    return jwt.encode(
        {"sub": "user-1", "iss": ISSUER, "iat": now, "exp": now + 300,
         "email": "a@b.ch", "tenant": tenant, "realm_access": {"roles": roles}},
        key, algorithm="RS256", headers={"kid": KID},
    )


def _install_auth(roles):
    key, jwks = _keypair_and_jwks()
    deps.set_verifier_override(KeycloakVerifier(OidcConfig(issuer=ISSUER), lambda: jwks))
    return _token(key, roles)


def teardown_function():
    deps.set_verifier_override(None)
    v1.set_vector_store(None)
    v1.set_mission_runner(None)


# ---- /models/route (öffentliche Policy, kein Auth) ----
def test_route_local_only_bleibt_lokal():
    r = client.post("/api/v1/models/route", json={"data_class": "local_only", "prompt_tokens_est": 10})
    assert r.status_code == 200
    assert r.json()["placement"] == "local"


def test_route_faehigkeit_fehlt_lokal_geht_cloud():
    r = client.post("/api/v1/models/route", json={
        "needs": ["vision"], "local_available": True, "local_capabilities": [], "cloud_available": True,
    })
    body = r.json()
    assert body["placement"] == "cloud" and body["fallback"] == "local"


# ---- /me (Auth-Kette) ----
def test_me_ohne_auth_konfiguration_ist_503():
    deps.set_verifier_override(None)  # Auth nicht konfiguriert
    r = client.get("/api/v1/me")
    assert r.status_code == 503


def test_me_ohne_token_ist_401():
    _install_auth(["member"])
    r = client.get("/api/v1/me")
    assert r.status_code == 401


def test_me_mit_ungueltigem_token_ist_401():
    _install_auth(["member"])
    r = client.get("/api/v1/me", headers={"authorization": "Bearer nonsense"})
    assert r.status_code == 401


def test_me_mit_gueltigem_token_liefert_principal():
    token = _install_auth(["member", "admin"])
    r = client.get("/api/v1/me", headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["subject"] == "user-1"
    assert body["tenant"] == "kunden"
    assert "admin" in body["roles"]


# ---- /knowledge/search (RBAC + Mandantentrennung) ----
def test_search_ohne_recht_ist_403():
    # 'outsider' hat keine Rolle → keine Rechte (Default-Deny).
    token = _install_auth(["outsider"])
    r = client.post("/api/v1/knowledge/search", json={"query": "x"},
                    headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_search_ohne_store_ist_503():
    token = _install_auth(["member"])  # member hat knowledge:read
    r = client.post("/api/v1/knowledge/search", json={"query": "x"},
                    headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 503


def test_search_ist_mandantengetrennt():
    store = InMemoryVectorStore()
    emb = v1._embedder
    store.upsert([
        Document(id="a1", tenant="kunden", text="Vertrag kuendigen", vector=emb.embed(["Vertrag kuendigen"])[0]),
        Document(id="b1", tenant="andere", text="Vertrag kuendigen", vector=emb.embed(["Vertrag kuendigen"])[0]),
    ])
    v1.set_vector_store(store)
    token = _install_auth(["member"], )  # tenant=kunden im Token
    r = client.post("/api/v1/knowledge/search", json={"query": "Vertrag", "k": 5},
                    headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200
    ids = {h["id"] for h in r.json()}
    assert "a1" in ids
    assert "b1" not in ids, "Mandantentrennung verletzt: fremdes Dokument sichtbar"


# ---- /knowledge/ingest (RBAC knowledge:write) ----
def test_ingest_ohne_recht_ist_403():
    token = _install_auth(["viewer"])  # viewer hat nur knowledge:read, nicht :write
    r = client.post("/api/v1/knowledge/ingest", json={"doc_id": "d1", "text": "abc"},
                    headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_ingest_dann_suche_findet_dokument_mandantengetrennt():
    store = InMemoryVectorStore()
    v1.set_vector_store(store)
    token = _install_auth(["member"])  # member: read + write + agent:run, tenant=kunden
    ing = client.post(
        "/api/v1/knowledge/ingest",
        json={"doc_id": "handbuch", "text": "Rueckgabe innerhalb 30 Tagen moeglich. " * 20},
        headers={"authorization": f"Bearer {token}"},
    )
    assert ing.status_code == 200
    assert ing.json()["chunks"] >= 1 and ing.json()["tenant"] == "kunden"
    # Suche im selben Mandanten findet es.
    r = client.post("/api/v1/knowledge/search", json={"query": "Rueckgabe", "k": 3},
                    headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200 and len(r.json()) >= 1
    # Fremder Mandant sieht nichts.
    other = _install_auth(["member"])  # neuer Verifier, tenant weiterhin kunden im Token
    # Token mit anderem Mandanten:
    key, jwks = _keypair_and_jwks()
    deps.set_verifier_override(KeycloakVerifier(OidcConfig(issuer=ISSUER), lambda: jwks))
    other = _token(key, ["member"], tenant="fremd")
    r2 = client.post("/api/v1/knowledge/search", json={"query": "Rueckgabe"},
                     headers={"authorization": f"Bearer {other}"})
    assert r2.status_code == 200 and r2.json() == []


# ---- /missions (RBAC agent:run) ----
def test_mission_ohne_recht_ist_403():
    token = _install_auth(["viewer"])  # viewer hat kein agent:run
    r = client.post("/api/v1/missions", json={"goal": "Hallo"},
                    headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_mission_mit_runner_liefert_ergebnis():
    v1.set_mission_runner(lambda goal, tenant: {
        "ok": True, "placement": "local", "reason": "test", "text": f"[{tenant}] {goal}", "error": None,
    })
    token = _install_auth(["member"])  # member hat agent:run
    r = client.post("/api/v1/missions", json={"goal": "Fasse zusammen"},
                    headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True and body["text"] == "[kunden] Fasse zusammen"


def test_mission_ohne_llm_ist_503():
    v1.set_mission_runner(lambda g, t: {"ok": False, "placement": "local", "reason": "x",
                                        "text": None, "error": "lokal gewählt, aber LOCAL_LLM_URL nicht gesetzt"})
    token = _install_auth(["member"])
    r = client.post("/api/v1/missions", json={"goal": "x"},
                    headers={"authorization": f"Bearer {token}"})
    assert r.status_code == 503
