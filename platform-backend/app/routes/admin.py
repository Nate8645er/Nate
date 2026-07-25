"""Provisionierung: Mandant anlegen + ersten API-Schluessel ausgeben.

Geschuetzt durch einen Admin-Token (Umgebungsvariable ADMIN_TOKEN)."""
from __future__ import annotations

import hmac
import os

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr

from ..provisioning import provision_tenant

router = APIRouter()


def _require_admin(x_admin_token: str) -> None:
    expected = os.environ.get("ADMIN_TOKEN", "")
    # Konstante-Zeit-Vergleich, und leerer/nicht gesetzter Token sperrt alles.
    if not expected or not hmac.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="Admin-Token ungueltig")


class ProvisionRequest(BaseModel):
    tenant_name: str
    owner_email: EmailStr
    plan_code: str


@router.post("/admin/provision")
async def provision(req: ProvisionRequest, x_admin_token: str = Header(default="")):
    _require_admin(x_admin_token)
    result = provision_tenant(req.tenant_name, req.owner_email, req.plan_code)
    result["note"] = "Diesen Schluessel sicher speichern — er wird nicht erneut angezeigt."
    return result
