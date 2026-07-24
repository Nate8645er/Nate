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

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..knowledge.embedding import HashingEmbedder
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


def set_vector_store(store: VectorStore | None) -> None:
    global _vector_store
    _vector_store = store


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
