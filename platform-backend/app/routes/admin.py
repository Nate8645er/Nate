"""Provisionierung: Mandant + Owner-Nutzer mit initialem Passwort anlegen.

Geschuetzt durch einen Admin-Token (Umgebungsvariable ADMIN_TOKEN). Es gibt
keinen API-Schluessel mehr -- das Passwort wird direkt hier gesetzt (Admin/Ops
teilt es dem Kunden out-of-band mit, z.B. telefonisch oder per separatem
Kanal), der Kunde meldet sich danach ganz normal per `/v1/auth/login` an."""
from __future__ import annotations

import hmac
import os

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field

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
    # bcrypt trunkiert Eingaben ab 72 Bytes stillschweigend -- statt das
    # Passwort ueber diese Grenze hinaus wirkungslos zu verlaengern, wird es
    # hier hart begrenzt (Grenze ist grosszuegig genug fuer jede realistische
    # Passphrase). Gleiche Grenzen wie `/v1/auth/signup` (SignupRequest).
    password: str = Field(min_length=8, max_length=72)


@router.post("/admin/provision")
async def provision(req: ProvisionRequest, x_admin_token: str = Header(default="")):
    _require_admin(x_admin_token)
    result = provision_tenant(
        req.tenant_name, req.owner_email, req.plan_code, password=req.password
    )
    return {
        "tenant_id": result["tenant_id"],
        "plan": result["plan"],
        "note": "Passwort dem Kunden out-of-band mitteilen -- Anmeldung ueber /v1/auth/login.",
    }
