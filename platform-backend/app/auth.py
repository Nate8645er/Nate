"""Authentifizierung: mandantengebundene API-Schluessel UND Web-Sessions.

Zwei gleichwertige Wege zum selben `Principal`:
  - `Authorization: Bearer <klartext-key>` -- Entwickler/API-Zugriff. Gespeichert
    wird nur der SHA-256-Hash, Lookup ueber `api_keys`.
  - Session-Cookie (HttpOnly) -- Web-Login per E-Mail+Passwort
    (`app/routes/auth.py`). Gespeichert wird nur der SHA-256-Hash des
    Session-Tokens, Lookup ueber `sessions`. Beide Tabellen sind bewusst NICHT
    RLS-gebunden -- Henne-Ei-Problem: der Mandant wird ja erst durch den
    Lookup bestimmt, RLS haette sich also selbst blockiert (der Fund setzt
    ausserdem in beiden Faellen bereits Kenntnis eines hochentropischen
    Geheimnisses voraus, nicht nur einer erratbaren ID).
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass

import bcrypt
from fastapi import Cookie, Header, HTTPException

# Name des Session-Cookies (siehe app/routes/auth.py) und Gueltigkeitsdauer.
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


def generate_key() -> tuple[str, str]:
    """Erzeugt (klartext, hash). Klartext wird dem Kunden genau einmal gezeigt."""
    clear = "pk_" + secrets.token_urlsafe(32)
    return clear, hash_key(clear)


def generate_session_token() -> tuple[str, str]:
    """Erzeugt (klartext, hash) fuer ein Session-Cookie. Gleiche Technik wie
    API-Keys (hochentropischer Zufallswert, nur der Hash landet in der DB) --
    anders als ein Passwort hat ein Session-Token volle Entropie, SHA-256
    reicht hier (kein Brute-Force-Ziel wie bei niedrigentropischen Passwoertern)."""
    clear = secrets.token_urlsafe(32)
    return clear, hash_key(clear)


def hash_password(password: str) -> str:
    """bcrypt statt SHA-256: Passwoerter haben niedrige Entropie (Menschen
    denken sie sich aus) und muessen absichtlich LANGSAM/Brute-Force-resistent
    gehasht werden -- SHA-256 waere hier falsch (das ist nur fuer die bereits
    hochentropischen API-Keys/Session-Tokens oben in Ordnung)."""
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


def _principal_from_api_key(token: str):
    key_hash = hash_key(token)

    from .db import admin_tx  # lazy: haelt dieses Modul ohne DB importierbar

    # Lookup laeuft ueber admin_tx (api_keys-Join braucht Tenant-uebergreifende
    # Sicht auf genau diese eine Zeile; RLS wuerde sich sonst selbst blockieren,
    # weil der Mandant erst hier bestimmt wird).
    with admin_tx() as conn:
        row = conn.execute(
            f"""
            SELECT {_PRINCIPAL_COLUMNS}
            FROM api_keys k
            JOIN tenants t ON t.id = k.tenant_id
            JOIN plans   p ON p.id = t.plan_id
            WHERE k.key_hash = %s
            """,
            (key_hash,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="Ungueltiger API-Schluessel")
        conn.execute(
            "UPDATE api_keys SET last_used_at = now() WHERE key_hash = %s", (key_hash,)
        )

    if row["status"] != "active":
        raise HTTPException(status_code=403, detail=f"Mandant {row['status']}")
    return _row_to_principal(row)


def _principal_from_session(token: str):
    token_hash = hash_key(token)

    from .db import admin_tx  # lazy, wie oben

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
    authorization: str = Header(default=""),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> Principal:
    """Bearer-API-Key ODER Session-Cookie -- beide fuehren zum selben
    `Principal`, der Rest der App (RLS, Tarif-Limits) unterscheidet nicht,
    wie authentifiziert wurde. Bearer hat Vorrang (unveraendertes Verhalten
    fuer bestehende API-Clients)."""
    if authorization.lower().startswith("bearer "):
        return _principal_from_api_key(authorization[7:].strip())
    if session:
        return _principal_from_session(session)
    raise HTTPException(
        status_code=401, detail="Anmeldung erforderlich (Bearer-Token oder Session-Cookie)"
    )
