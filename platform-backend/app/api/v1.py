"""HTTP-API v1 — macht die getestete Fachlogik über HTTP nutzbar.

Cutover-Fundament: die bestehende Vercel-App (oder jeder Client) kann das neue
Backend über eine versionierte, auth-geschützte API ansprechen. Additiv; die
Health-/Metrics-Endpunkte bleiben unverändert.

Endpunkte:
- `GET  /api/v1/me`              — verifizierter Principal (Auth-Kette-Beweis).
- `POST /api/v1/models/route`    — reine Routing-Entscheidung (keine Daten, kein
                                   Auth nötig — nur Policy + Begründung).
- `POST /api/v1/knowledge/search`— mandantengetrennte Vektor-Suche (RBAC:
                                   knowledge:read). Ehrlich 503, wenn kein
                                   VectorStore verbunden ist.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..knowledge.embedding import HashingEmbedder
from ..knowledge.ingest import IngestPipeline
from ..knowledge.retrieval import Retriever
from ..knowledge.vectorstore import VectorStore
from ..models.router import DataClass, ModelRequest, RoutingContext, decide
from ..platform.auth import Principal
from ..platform.rbac import Permission
from .deps import require_permission, require_principal

router = APIRouter(prefix="/api/v1", tags=["v1"])

#: Optionaler, prozessweit injizierter VectorStore (Tests/Betrieb setzen ihn).
_vector_store: VectorStore | None = None
_embedder = HashingEmbedder(dim=256)

#: Mission-Runner: (goal, tenant) -> {"ok", "placement", "reason", "text", "error"}.
#: Injizierbar (Tests/Betrieb); None → Standard-Runner über den ModelRouter.
MissionRunner = Callable[[str, str], dict]
_mission_runner: MissionRunner | None = None


def set_vector_store(store: VectorStore | None) -> None:
    global _vector_store
    _vector_store = store


def set_mission_runner(runner: MissionRunner | None) -> None:
    global _mission_runner
    _mission_runner = runner


def _default_mission_runner(goal: str, tenant: str) -> dict:
    """Führt eine Mission als echte Completion über den ModelRouter aus.

    Ehrlich: Ist kein LLM konfiguriert/erreichbar, liefert der Router
    `ok=False` mit Begründung — kein erfundenes Ergebnis.
    """
    from ..config import get_settings
    from ..models.router import ModelRouter

    s = get_settings()
    ctx = RoutingContext(local_available=s.local_llm.configured, cloud_available=False)
    router_ = ModelRouter(ctx, local_base_url=s.local_llm.url)
    req = ModelRequest(prompt_tokens_est=max(1, len(goal) // 4), data_class=DataClass.INTERNAL)
    result = router_.complete(req, messages=[{"role": "user", "content": goal}])
    decision = result.get("decision", {})
    if not result.get("ok"):
        return {"ok": False, "placement": decision.get("placement"), "reason": decision.get("reason"),
                "text": None, "error": result.get("error", "unbekannt")}
    text = ""
    try:
        text = result["response"].choices[0].message.content
    except Exception:  # noqa: BLE001
        text = str(result.get("response", ""))
    return {"ok": True, "placement": decision.get("placement"), "reason": decision.get("reason"),
            "text": text, "error": None}


# --------------------------------------------------------------------------- #
# /me — Auth-Kette
# --------------------------------------------------------------------------- #
class MeResponse(BaseModel):
    subject: str
    tenant: str | None
    roles: list[str]
    email: str | None


@router.get("/me", response_model=MeResponse)
def me(principal: Principal = Depends(require_principal)) -> MeResponse:
    return MeResponse(
        subject=principal.subject,
        tenant=principal.tenant,
        roles=sorted(principal.roles),
        email=principal.email,
    )


# --------------------------------------------------------------------------- #
# /models/route — reine Policy
# --------------------------------------------------------------------------- #
class RouteRequest(BaseModel):
    prompt_tokens_est: int = Field(ge=0, default=0)
    data_class: DataClass = DataClass.INTERNAL
    needs: list[str] = Field(default_factory=list)
    local_available: bool = True
    local_capabilities: list[str] = Field(default_factory=list)
    cloud_available: bool = True
    local_load_pct: float = 0.0


class RouteResponse(BaseModel):
    placement: str
    reason: str
    fallback: str | None


@router.post("/models/route", response_model=RouteResponse)
def route_model(body: RouteRequest) -> RouteResponse:
    req = ModelRequest(
        prompt_tokens_est=body.prompt_tokens_est,
        data_class=body.data_class,
        needs=frozenset(body.needs),
    )
    ctx = RoutingContext(
        local_available=body.local_available,
        local_capabilities=frozenset(body.local_capabilities),
        cloud_available=body.cloud_available,
        local_load_pct=body.local_load_pct,
    )
    d = decide(req, ctx)
    return RouteResponse(placement=d.placement, reason=d.reason, fallback=d.fallback)


# --------------------------------------------------------------------------- #
# /knowledge/search — mandantengetrennt, RBAC-geschützt
# --------------------------------------------------------------------------- #
class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    k: int = Field(ge=1, le=50, default=5)


class SearchHit(BaseModel):
    id: str
    score: float
    text: str


@router.post("/knowledge/search", response_model=list[SearchHit])
def knowledge_search(
    body: SearchRequest,
    principal: Principal = Depends(require_permission(Permission.KNOWLEDGE_READ)),
) -> list[SearchHit]:
    if _vector_store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Wissens-Backend nicht verbunden (kein VectorStore konfiguriert)",
        )
    if not principal.tenant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Mandant im Token")
    retriever = Retriever(_vector_store, _embedder)
    # Isolation: die Suche ist fest auf den Mandanten des Tokens gebunden.
    hits = retriever.retrieve(principal.tenant, body.query, k=body.k)
    return [SearchHit(id=h.document.id, score=h.score, text=h.document.text) for h in hits]


# --------------------------------------------------------------------------- #
# /knowledge/ingest — Rohtext → Chunks → Embeddings → Store (RBAC knowledge:write)
# --------------------------------------------------------------------------- #
class IngestRequest(BaseModel):
    doc_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    metadata: dict = Field(default_factory=dict)


class IngestResponse(BaseModel):
    doc_id: str
    tenant: str
    chunks: int


@router.post("/knowledge/ingest", response_model=IngestResponse)
def knowledge_ingest(
    body: IngestRequest,
    principal: Principal = Depends(require_permission(Permission.KNOWLEDGE_WRITE)),
) -> IngestResponse:
    if _vector_store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Wissens-Backend nicht verbunden (kein VectorStore konfiguriert)",
        )
    if not principal.tenant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Mandant im Token")
    pipeline = IngestPipeline(_vector_store, _embedder)
    # Isolation: Dokument wird fest dem Mandanten des Tokens zugeschrieben.
    res = pipeline.ingest(principal.tenant, body.doc_id, body.text, body.metadata)
    return IngestResponse(doc_id=res.doc_id, tenant=res.tenant, chunks=res.chunks)


# --------------------------------------------------------------------------- #
# /missions — Auftrag ausführen (RBAC agent:run). Ehrlich 503 ohne LLM.
# --------------------------------------------------------------------------- #
class MissionRequest(BaseModel):
    goal: str = Field(min_length=1)


class MissionResponse(BaseModel):
    ok: bool
    placement: str | None
    reason: str | None
    text: str | None
    error: str | None


@router.post("/missions", response_model=MissionResponse)
def run_mission(
    body: MissionRequest,
    principal: Principal = Depends(require_permission(Permission.AGENT_RUN)),
) -> MissionResponse:
    if not principal.tenant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kein Mandant im Token")
    runner = _mission_runner or _default_mission_runner
    result = runner(body.goal, principal.tenant)
    if not result.get("ok"):
        # Nicht konfiguriert/erreichbar → 503 (ehrlich), kein erfundenes Ergebnis.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Mission nicht ausführbar: {result.get('error', 'kein LLM verbunden')}",
        )
    return MissionResponse(**{k: result.get(k) for k in ("ok", "placement", "reason", "text", "error")})
