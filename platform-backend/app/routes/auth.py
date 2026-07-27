"""Web-Login per E-Mail+Passwort -- der EINZIGE Authentifizierungspfad der
Plattform (siehe `app/auth.py`). Der frueher parallel existierende
`Authorization: Bearer pk_...`-API-Schluessel ist vollstaendig entfernt
(Migration `013_drop_api_keys.sql`).

Loest zwei Luecken auf einmal:
  - Bisher gab es UEBERHAUPT keinen Weg, sich selbst fuer den Free-Tarif
    anzumelden (nur `/admin/provision`, admin-token-geschuetzt, und die
    Stripe/Shopify-Webhooks) -- `/v1/auth/signup` legt jetzt einen
    Free-Tarif-Mandanten selbst an, wie es die Store-FAQ bereits verspricht.
  - Bisher musste sich JEDER Kunde einen rohen `pk_...`-Key ins Chat-UI
    einfuegen. `/v1/auth/login` gibt stattdessen ein HttpOnly-Session-Cookie
    aus -- der Client sieht nie ein Geheimnis, das er selbst verwalten
    muesste.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field

from ..auth import (
    DUMMY_PASSWORD_HASH,
    SESSION_COOKIE_NAME,
    create_session,
    hash_key,
    hash_password,
    set_session_cookie,
    verify_password,
)
from ..db import admin_tx, tenant_tx
from ..provisioning import provision_tenant
from ..ratelimit import (
    client_ip,
    login_limiter_email,
    login_limiter_ip,
    signup_limiter,
    signup_limiter_email,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])

_GENERIC_LOGIN_ERROR = "E-Mail oder Passwort falsch"

# Fixer Sentinel-Mandant fuer die Timing-Dummy-Rundreise im Login (siehe
# login() unten) -- eine echte, aber garantiert nie einem Nutzer gehoerende
# UUID (die Nil-UUID kommt aus gen_random_uuid() praktisch nie heraus).
# Muss keine echte Zeile in `tenants` haben: `tenant_tx` setzt nur eine
# Session-Variable, es gibt keinen Fremdschluessel-Zwang dafuer.
_TIMING_SENTINEL_TENANT_ID = "00000000-0000-0000-0000-000000000000"
_TIMING_SENTINEL_USER_ID = "00000000-0000-0000-0000-000000000000"


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


def _claim_existing_account(email_lower: str, password: str) -> dict | None:
    """Kritischer Sicherheitsfund (Fix, siehe app/provisioning.py):
    `provision_tenant()` reserviert JEDE E-Mail sofort in `user_directory`,
    auch ohne Passwort (Stripe-/Shopify-Kauf ohne Passwort-Feld im
    Checkout). Ohne diese Funktion wuerde ein Signup mit einer solchen
    E-Mail einfach mit 409 abgelehnt -- der ECHTE Eigentuemer (der noch nie
    ein Passwort gesetzt hat) haette dann KEINEN Weg mehr, sich jemals per
    Passwort anzumelden, sobald seine Autologin-Session (Checkout-Handoff)
    abgelaufen ist.

    Zwei Faelle, sobald die E-Mail bereits in `user_directory` steht:
      - `users.password_hash` ist NULL  -> das ist der echte Eigentuemer,
        der jetzt sein erstes Passwort setzt ("Konto beanspruchen"). Setzt
        das Passwort auf dem BESTEHENDEN Nutzer, legt eine Session fuer den
        BESTEHENDEN Mandanten an -- kein neuer Mandant.
      - `users.password_hash` ist bereits gesetzt -> echter Doppel-Versuch.

    Gibt `None` zurueck, wenn die E-Mail unbekannt ist ODER bereits ein
    Passwort existiert -- der Aufrufer faehrt dann mit dem normalen
    Neu-Anlage-Pfad (`provision_tenant`) fort, der im zweiten Fall ganz
    regulaer mit 409 scheitert (UniqueViolation auf `user_directory`).

    Bekanntes Restrisiko OHNE E-Mail-Verifikation (siehe README): wer zuerst
    hier ankommt, beansprucht das Konto. Strukturell dasselbe Problem wie
    der urspruengliche Fund, aber zeitlich VOR statt NACH dem ersten
    Kauf-Ereignis -- ein deutlich kleineres Fenster (der Angreifer muesste
    schneller sein als der zahlende Kunde selbst, nicht nur irgendwann
    innerhalb von 30 Tagen zuschlagen), aber nicht null."""
    with admin_tx() as conn:
        directory_row = conn.execute(
            "SELECT tenant_id, user_id FROM user_directory WHERE email_lower = %s",
            (email_lower,),
        ).fetchone()
    if directory_row is None:
        return None

    tenant_id = str(directory_row["tenant_id"])
    user_id = str(directory_row["user_id"])

    with tenant_tx(tenant_id) as conn:
        user = conn.execute(
            "SELECT password_hash FROM users WHERE id = %s", (user_id,)
        ).fetchone()
        if user is None or user["password_hash"] is not None:
            # Kein beanspruchbares Konto (Doppel-Versuch, oder -- durch die
            # Fremdschluessel praktisch ausgeschlossen -- ein verwaister
            # Directory-Eintrag). Aufrufer nimmt den regulaeren 409-Pfad.
            return None
        conn.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (hash_password(password), user_id),
        )
        plan_row = conn.execute(
            "SELECT p.code FROM tenants t JOIN plans p ON p.id = t.plan_id WHERE t.id = %s",
            (tenant_id,),
        ).fetchone()
        plan_code = plan_row["code"] if plan_row else "free"

    with admin_tx() as conn:
        session_token = create_session(conn, tenant_id, user_id)

    return {"tenant_id": tenant_id, "plan": plan_code, "session_token": session_token}


@router.post("/signup")
async def signup(req: SignupRequest, request: Request, response: Response):
    """Legt einen NEUEN Free-Tarif-Mandanten + Owner-Nutzer mit Passwort an
    und meldet ihn direkt per Session-Cookie an -- AUSSER die E-Mail ist
    bereits einem passwortlos angelegten Mandanten zugeordnet: dann wird
    stattdessen dieses bestehende Konto beansprucht (siehe
    `_claim_existing_account`)."""
    email_lower = str(req.email).lower()
    signup_limiter.check(client_ip(request))
    signup_limiter_email.check(email_lower)

    claimed = _claim_existing_account(email_lower, req.password)
    if claimed is not None:
        set_session_cookie(response, claimed["session_token"])
        return {
            "status": "ok",
            "tenant_id": claimed["tenant_id"],
            "plan": claimed["plan"],
            "claimed": True,
        }

    with admin_tx() as conn:
        # provision_tenant() haelt Passwort-Hash + user_directory-Eintrag
        # (inkl. 409 bei doppelter E-Mail) an EINER Stelle -- siehe
        # app/provisioning.py, genutzt auch von /admin/provision.
        result = provision_tenant(
            tenant_name=req.name, owner_email=str(req.email), plan_code="free",
            password=req.password, conn=conn,
        )
        tenant_id = result["tenant_id"]
        user_id = result["user_id"]
        session_token = create_session(conn, tenant_id, user_id)

    set_session_cookie(response, session_token)
    return {"status": "ok", "tenant_id": tenant_id, "plan": "free"}


@router.post("/login")
async def login(req: LoginRequest, request: Request, response: Response):
    """Prueft E-Mail+Passwort und setzt bei Erfolg ein neues Session-Cookie.
    Bei Fehlschlag IMMER dieselbe generische Meldung -- ob die E-Mail
    existiert oder nur das Passwort falsch war, ist von aussen nicht
    unterscheidbar (weder am Text noch (bestmoeglich) an der Laufzeit)."""
    ip = client_ip(request)
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
        # Timing-Konstanz (Security-Review, Punkt A): der "E-Mail bekannt"-
        # Zweig macht NACH dem admin_tx()-Lookup zusaetzlich eine ZWEITE
        # DB-Rundreise (tenant_tx, um password_hash zu lesen) vor dem
        # bcrypt-Vergleich. Ohne eine aequivalente Dummy-Rundreise hier waere
        # dieser Zweig messbar SCHNELLER (eine DB-Rundreise weniger) als der
        # "E-Mail bekannt, Passwort falsch"-Zweig -- ein Timing-Seitenkanal,
        # der genau das unterlaeuft, was dieser Kommentarblock verspricht
        # ("nie verraten, ob die E-Mail existiert"). Fix: gegen eine feste,
        # garantiert nie existierende Sentinel-Tenant/User-Kombination
        # dieselbe Art Rundreise ausfuehren -- RLS filtert sie ohnehin auf
        # 0 Zeilen (kein Fremdschluessel-Zwang bei set_config, siehe
        # app/db.py::tenant_tx).
        with tenant_tx(_TIMING_SENTINEL_TENANT_ID) as conn:
            conn.execute(
                "SELECT password_hash FROM users WHERE id = %s",
                (_TIMING_SENTINEL_USER_ID,),
            ).fetchone()
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
        session_token = create_session(conn, tenant_id, user_id)

    set_session_cookie(response, session_token)
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
