"""Web-Login per E-Mail+Passwort (Selbstbedienung) -- Ergaenzung zum
bestehenden Bearer-API-Key-Pfad (`app/auth.py`), nicht dessen Ersatz.

Loest zwei Luecken auf einmal:
  - Bisher gab es UEBERHAUPT keinen Weg, sich selbst fuer den Free-Tarif
    anzumelden (nur `/admin/provision`, admin-token-geschuetzt, und die
    Stripe/Shopify-Webhooks) -- `/v1/auth/signup` legt jetzt einen
    Free-Tarif-Mandanten selbst an, wie es die Store-FAQ bereits verspricht.
  - Bisher musste sich JEDER Kunde einen rohen `pk_...`-Key ins Chat-UI
    einfuegen. `/v1/auth/login` gibt stattdessen ein HttpOnly-Session-Cookie
    aus -- der Client sieht den Roh-Key fuer diesen Pfad nie.

Der API-Key bleibt fuer Entwickler/Automatisierung unveraendert nutzbar
(`app/auth.py::require_principal` akzeptiert weiterhin `Authorization: Bearer
pk_...`); dieser Router ist ausschliesslich der neue Web-Login-Pfad.
"""
from __future__ import annotations

import datetime as dt

import psycopg
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field

from ..auth import (
    DUMMY_PASSWORD_HASH,
    SESSION_COOKIE_NAME,
    SESSION_TTL_DAYS,
    generate_session_token,
    hash_key,
    hash_password,
    verify_password,
)
from ..db import admin_tx, tenant_tx
from ..provisioning import provision_tenant
from ..ratelimit import login_limiter_email, login_limiter_ip, signup_limiter

router = APIRouter(prefix="/v1/auth", tags=["auth"])

_GENERIC_LOGIN_ERROR = "E-Mail oder Passwort falsch"


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    # bcrypt trunkiert Eingaben ab 72 Bytes stillschweigend -- statt das
    # Passwort ueber diese Grenze hinaus wirkungslos zu verlaengern, wird es
    # hier hart begrenzt (Grenze ist grosszuegig genug fuer jede realistische
    # Passphrase).
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _set_session_cookie(response: Response, token: str) -> None:
    # HttpOnly: per JavaScript nicht auslesbar (kein XSS-Diebstahl des
    # Session-Tokens). Secure: nur ueber HTTPS uebertragen. SameSite=Lax:
    # bewusste, dokumentierte CSRF-Haltung fuer diese Runde -- schuetzt gegen
    # die meisten Cross-Site-Faelle (Cookie wird bei einfachen Cross-Site-
    # Requests wie <img>/<form> NICHT mitgeschickt), ohne ein zusaetzliches
    # CSRF-Token einzufuehren. Reicht fuer eine Same-Origin-App ohne
    # Cross-Site-Formulare; kein Ersatz fuer ein echtes CSRF-Token, sollte
    # diese App spaeter Cross-Site-Einbettung brauchen.
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=SESSION_TTL_DAYS * 86400,
        path="/",
    )


def _create_session(conn, tenant_id: str, user_id: str) -> str:
    """Legt eine neue Session in der uebergebenen Transaktion an und gibt den
    KLARTEXT-Token zurueck (wird nur als Cookie an den Client gereicht, nie
    gespeichert)."""
    token, token_hash = generate_session_token()
    expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=SESSION_TTL_DAYS)
    conn.execute(
        "INSERT INTO sessions (token_hash, tenant_id, user_id, expires_at) "
        "VALUES (%s, %s, %s, %s)",
        (token_hash, tenant_id, user_id, expires_at),
    )
    return token


@router.post("/signup")
async def signup(req: SignupRequest, request: Request, response: Response):
    """Legt einen NEUEN Free-Tarif-Mandanten + Owner-Nutzer mit Passwort an
    und meldet ihn direkt per Session-Cookie an -- kein API-Key wird an den
    Client gereicht (anders als `/admin/provision`)."""
    signup_limiter.check(_client_ip(request))

    email_lower = req.email.lower()
    with admin_tx() as conn:
        result = provision_tenant(
            tenant_name=req.name, owner_email=str(req.email), plan_code="free", conn=conn
        )
        tenant_id = result["tenant_id"]
        user_id = result["user_id"]

        conn.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (hash_password(req.password), user_id),
        )
        try:
            conn.execute(
                "INSERT INTO user_directory (email_lower, tenant_id, user_id) "
                "VALUES (%s, %s, %s)",
                (email_lower, tenant_id, user_id),
            )
        except psycopg.errors.UniqueViolation as exc:
            # Rollback der gesamten Transaktion (inkl. gerade angelegtem
            # Mandanten) -- kein verwaister Mandant bei doppelter E-Mail.
            raise HTTPException(
                status_code=409, detail="Diese E-Mail-Adresse ist bereits registriert"
            ) from exc

        session_token = _create_session(conn, tenant_id, user_id)

    _set_session_cookie(response, session_token)
    return {"status": "ok", "tenant_id": tenant_id, "plan": "free"}


@router.post("/login")
async def login(req: LoginRequest, request: Request, response: Response):
    """Prueft E-Mail+Passwort und setzt bei Erfolg ein neues Session-Cookie.
    Bei Fehlschlag IMMER dieselbe generische Meldung -- ob die E-Mail
    existiert oder nur das Passwort falsch war, ist von aussen nicht
    unterscheidbar (weder am Text noch (bestmoeglich) an der Laufzeit)."""
    ip = _client_ip(request)
    email_lower = req.email.lower()
    # Beide Richtungen pruefen -- entweder kann zuerst zuschlagen.
    login_limiter_ip.check(ip)
    login_limiter_email.check(email_lower)

    with admin_tx() as conn:
        # user_directory ist NICHT RLS-gebunden (Henne-Ei: der Mandant ist ja
        # erst das Ergebnis dieses Lookups) und enthaelt bewusst kein
        # Geheimnis -- nur die Zuordnung E-Mail -> (tenant_id, user_id).
        row = conn.execute(
            "SELECT tenant_id, user_id FROM user_directory WHERE email_lower = %s",
            (email_lower,),
        ).fetchone()

    if row is None:
        # Timing-Konstanz: derselbe bcrypt-Vergleich laeuft auch, wenn die
        # E-Mail unbekannt ist (siehe Kommentar bei DUMMY_PASSWORD_HASH).
        verify_password(req.password, DUMMY_PASSWORD_HASH)
        raise HTTPException(status_code=401, detail=_GENERIC_LOGIN_ERROR)

    tenant_id = str(row["tenant_id"])
    user_id = str(row["user_id"])

    # Ab hier ganz normal RLS-konform: tenant_id ist jetzt bekannt, der
    # password_hash wird ueber den regulaeren, mandantengebundenen Pfad
    # gelesen (siehe Migrationskommentar zu resolve_metadata_tenant).
    with tenant_tx(tenant_id) as conn:
        user = conn.execute(
            "SELECT password_hash FROM users WHERE id = %s", (user_id,)
        ).fetchone()

    pw_hash = user["password_hash"] if user else None
    if not pw_hash or not verify_password(req.password, pw_hash):
        if not pw_hash:
            verify_password(req.password, DUMMY_PASSWORD_HASH)
        raise HTTPException(status_code=401, detail=_GENERIC_LOGIN_ERROR)

    with admin_tx() as conn:
        session_token = _create_session(conn, tenant_id, user_id)

    _set_session_cookie(response, session_token)
    return {"status": "ok", "tenant_id": tenant_id}


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Loescht die Session serverseitig (falls vorhanden) und das Cookie.
    Absichtlich ohne require_principal-Abhaengigkeit -- ein Logout mit
    bereits abgelaufener/unbekannter Session soll trotzdem klaglos 200
    liefern und das Cookie loeschen, statt mit 401 zu scheitern."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        with admin_tx() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = %s", (hash_key(token),))
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"status": "ok"}
