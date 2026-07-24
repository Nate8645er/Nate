"""GET /v1/models — die im Tarif des Mandanten freigeschalteten Modelle.
Treibt den Modellwechsel im UI."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import Principal, require_principal
from ..models_catalog import models_for_plan

router = APIRouter()


@router.get("/v1/models")
async def list_models(principal: Principal = Depends(require_principal)):
    return {
        "plan": principal.plan_code,
        "models": models_for_plan(principal.allowed_models),
    }
