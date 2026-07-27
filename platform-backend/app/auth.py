"""Authentifizierung: ausschliesslich Web-Sessions (HttpOnly-Cookie).

Es gibt EINEN Weg zu einem `Principal`:
  - Session-Cookie (HttpOnly) -- Web-Login per E-Mail+Passwort
    (`app/routes/auth.py`, `app/routes/billing.py` fuer den Stripe-
    Checkout-Autologin). Gespeichert wird nur der SHA-256-Hash des
    Session-Tokens, Lookup ueber `sessions`. Diese Tabelle ist bewusst
    NICHT RLS-gebunden -- Henne-Ei-Problem: der Mandant wird ja erst durch
    den Lookup bestimmt, RLS haette sich also selbst blockiert (der Fund
    setzt ausserdem bereits Kenntnis eines hochentropischen Geheimnisses
    voraus, nicht nur einer erratbaren ID).

Der frueher parallel existierende `Authorization: Bearer pk_...`-API-
Schluessel-Pfad (Entwickler-/Programmzugriff) ist bewusst entfernt worden --
siehe Migration `013_drop_api_keys.sql` und `app/provisioning.py`. Es gibt
keinen Weg mehr, sich ohne Browser-Session zu authentifizieren.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import secrets
from dataclasses import dataclass

import bcrypt
from fastapi import Cookie, HTTPException, Response

# Name des Session-Cookies und Gueltigkeitsdauer.
SESSION_COOKIE_NAME = "session"
SESSION_TTL_DAYS = 30


@dataclass
class Principal:
    tenant_id: str
    tenant_name: str
    plan_code: str
    allowed_models: list
    monthly_token_limit: int
    max_agents: int
    status: str
    stripe_customer_id: str | None = None


def hash_key(clear: str) -> str:
    return hashlib.sha256(clear.encode("utf-8")).hexdigest()


def generate_session_token() -> tuple[str, str]:
    """Erzeugt (klartext, hash) fuer ein Session-Cookie. Hochentropischer
    Zufallswert (secrets.token_urlsafe(32), 256 Bit) -- SHA-256 auf den Hash
    reicht hier (kein Brute-Force-Ziel wie bei niedrigentropischen
    Passwoertern), nur der Hash landet in der DB."""
    clear = secrets.token_urlsafe(32)
    return clear, hash_key(clear)


def hash_password(password: str) -> str:
    """bcrypt statt SHA-256: Passwoerter haben niedrige Entropie (Menschen
    denken sie sich aus) und muessen absichtlich LANGSAM/Brute-Force-resistent
    gehasht werden -- SHA-256 waere hier falsch (das ist nur fuer die bereits
    hochentropischen Session-Tokens oben in Ordnung)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    """Timing-sicher (bcrypt.checkpw) von Haus aus. Ein defekter/fremdformatiger
    Hash darf niemals eine Exception nach aussen werfen (die sonst as 500
    durchschlagen wuerde) -- einfach als "falsch" werten."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# Fixer Dummy-Hash fuer den Fall "E-Mail unbekannt" beim Login: ein bcrypt-
# Vergleich gegen einen echten Hash braucht ungefaehr gleich lange wie gegen
# den Hash eines existierenden Nutzers -- ohne das wuerde eine unbekannte
# E-Mail (kein Hash zum Vergleichen vorhanden) messbar SCHNELLER antworten
# als eine bekannte E-Mail mit falschem Passwort, was das "nie verraten ob
# die E-Mail existiert"-Ziel per Timing-Seitenkanal unterlaufen wuerde.
DUMMY_PASSWORD_HASH = hash_password("nur-fuer-timing-konstanz-nie-echt-verwendet")


def create_session(conn, tenant_id: str, user_id: str) -> str:
    """Legt eine neue Session in der uebergebenen Transaktion an und gibt den
    KLARTEXT-Token zurueck (wird nur als Cookie an den Client gereicht, nie
    gespeichert). Gemeinsam genutzt von `app/routes/auth.py` (Signup/Login)
    und `app/routes/billing.py` (Stripe-Checkout-Autologin ohne Passwort) --
    an EINER Stelle definiert, damit Session-Erzeugung nicht dupliziert
    wird."""
    token, token_hash = generate_session_token()
    expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=SESSION_TTL_DAYS)
    conn.execute(
        "INSERT INTO sessions (token_hash, tenant_id, user_id, expires_at) "
        "VALUES (%s, %s, %s, %s)",
        (token_hash, tenant_id, user_id, expires_at),
    )
    return token


def set_session_cookie(response: Response, token: str) -> None:
    """Setzt das HttpOnly-Session-Cookie auf der uebergebenen Response.
    Gemeinsam genutzt von `app/routes/auth.py` und `app/routes/billing.py`
    (Checkout-Claim).

    HttpOnly: per JavaScript nicht auslesbar (kein XSS-Diebstahl des
    Session-Tokens). Secure: nur ueber HTTPS uebertragen. SameSite=Lax:
    bewusste, dokumentierte CSRF-Haltung fuer diese Runde -- schuetzt gegen
    die meisten Cross-Site-Faelle (Cookie wird bei einfachen Cross-Site-
    Requests wie <img>/<form> NICHT mitgeschickt), ohne ein zusaetzliches
    CSRF-Token einzufuehren. Reicht fuer eine Same-Origin-App ohne
    Cross-Site-Formulare; kein Ersatz fuer ein echtes CSRF-Token, sollte
    diese App spaeter Cross-Site-Einbettung brauchen."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=SESSION_TTL_DAYS * 86400,
        path="/",
    )


def _row_to_principal(row) -> Principal:
    return Principal(
        tenant_id=str(row["tenant_id"]),
        tenant_name=row["tenant_name"],
        plan_code=row["plan_code"],
        allowed_models=row["allowed_models"],
        monthly_token_limit=int(row["monthly_token_limit"]),
        max_agents=int(row["max_agents"]),
        status=row["status"],
        stripe_customer_id=row["stripe_customer_id"],
    )


_PRINCIPAL_COLUMNS = """
    t.id AS tenant_id, t.name AS tenant_name, t.status AS status,
    t.stripe_customer_id AS stripe_customer_id,
    p.code AS plan_code, p.allowed_models, p.monthly_token_limit,
    p.max_agents
"""


def _principal_from_session(token: str):
    token_hash = hash_key(token)

    from .db import admin_tx  # lazy: haelt dieses Modul ohne DB importierbar

    with admin_tx() as conn:
        row = conn.execute(
            f"""
            SELECT {_PRINCIPAL_COLUMNS}
            FROM sessions s
            JOIN tenants t ON t.id = s.tenant_id
            JOIN plans   p ON p.id = t.plan_id
            WHERE s.token_hash = %s AND s.expires_at > now()
            """,
            (token_hash,),
        ).fetchone()
        if row is None:
            # Unbekannt UND abgelaufen laufen bewusst im selben Zweig: beides
            # ist fuer den Client ein einfaches "bitte neu anmelden" (401),
            # keine Unterscheidung noetig oder gewuenscht.
            raise HTTPException(status_code=401, detail="Sitzung ungueltig oder abgelaufen")
        conn.execute(
            "UPDATE sessions SET last_used_at = now() WHERE token_hash = %s", (token_hash,)
        )

    if row["status"] != "active":
        raise HTTPException(status_code=403, detail=f"Mandant {row['status']}")
    return _row_to_principal(row)


async def require_principal(
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> Principal:
    """Ausschliesslich Session-Cookie -- kein Bearer-Token-Pfad mehr. Fehlt
    das Cookie oder ist es ungueltig/abgelaufen, ist das Ergebnis in beiden
    Faellen 401 (kein Unterschied nach aussen, siehe `_principal_from_session`)."""
    if session:
        return _principal_from_session(session)
    raise HTTPException(status_code=401, detail="Anmeldung erforderlich (Session-Cookie)")
