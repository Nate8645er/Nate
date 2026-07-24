"""Verbrauchsanzeige pro Mandant — Grundlage fuer die spaetere Abrechnung
(Phase 4) und die Nutzungsanzeige im Kundenkonto."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import Principal, require_principal
from ..db import tenant_tx

router = APIRouter()


@router.get("/v1/usage")
async def usage(principal: Principal = Depends(require_principal)):
    with tenant_tx(principal.tenant_id) as conn:
        month = conn.execute(
            """
            SELECT COALESCE(SUM(tokens_in), 0)  AS tokens_in,
                   COALESCE(SUM(tokens_out), 0) AS tokens_out,
                   COUNT(*)                      AS calls
            FROM usage_events
            WHERE tenant_id = %s AND ts >= date_trunc('month', now())
            """,
            (principal.tenant_id,),
        ).fetchone()
        by_model = conn.execute(
            """
            SELECT model,
                   SUM(tokens_in)  AS tokens_in,
                   SUM(tokens_out) AS tokens_out
            FROM usage_events
            WHERE tenant_id = %s AND ts >= date_trunc('month', now())
            GROUP BY model
            ORDER BY 2 DESC
            """,
            (principal.tenant_id,),
        ).fetchall()

    used = int(month["tokens_in"]) + int(month["tokens_out"])
    return {
        "tenant": principal.tenant_name,
        "plan": principal.plan_code,
        "month": {
            "tokens_in": int(month["tokens_in"]),
            "tokens_out": int(month["tokens_out"]),
            "tokens_total": used,
            "calls": int(month["calls"]),
            "limit": principal.monthly_token_limit,
            "remaining": max(0, principal.monthly_token_limit - used),
        },
        "by_model": [
            {
                "model": r["model"],
                "tokens_in": int(r["tokens_in"]),
                "tokens_out": int(r["tokens_out"]),
            }
            for r in by_model
        ],
    }
