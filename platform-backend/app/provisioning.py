"""Gemeinsame Provisionierungs-Logik: Mandant + Owner-Nutzer anlegen.
Genutzt von der Admin-Route, dem Store-Webhook und dem Stripe-Checkout.

Es gibt keinen API-Schluessel mehr (siehe Migration `013_drop_api_keys.sql`
und `app/auth.py`) -- der einzige Weg zu einem `Principal` ist eine
Web-Session. `provision_tenant()` deckt zwei Faelle ab, reserviert die
E-Mail in `user_directory` aber in BEIDEN FAELLEN SOFORT:

  1. Ein Passwort liegt sofort vor (`/admin/provision` mit Pflicht-Feld
     `password`, `/v1/auth/signup`) -- wird direkt gehasht gesetzt.
  2. Noch kein Passwort vorhanden (Stripe-/Shopify-Checkout-Webhook: der
     Kunde hat im Checkout-Formular kein Passwort vergeben) -- der Aufrufer
     erzeugt stattdessen selbst per `app.auth.create_session` eine Session
     (siehe `app/routes/billing.py`).

  In BEIDEN Faellen wird die E-Mail SOFORT (ohne Passwort) in
  `user_directory` eingetragen (Sicherheits-Fix, siehe unten) -- das ist der
  einzige Unterschied zur fruaeheren Version dieses Moduls, der zaehlt.

  SICHERHEITS-FUND (behoben): Frueher wurde `user_directory` NUR gesetzt,
  wenn `password` uebergeben wurde. Ein passwortlos provisionierter Nutzer
  (Fall 2) hatte deshalb KEINEN `user_directory`-Eintrag -- die 409-
  Doppelregistrierungs-Sperre in `/v1/auth/signup` griff fuer seine E-Mail
  also gar nicht. Ein Angreifer, der nur die E-Mail-Adresse eines zahlenden
  Kunden kennt, konnte sich selbst per `/v1/auth/signup` mit GENAU dieser
  E-Mail registrieren und bekam einen `user_directory`-Eintrag, der die
  E-Mail auf seinen eigenen, neuen Mandanten zeigte -- der echte Kunde
  verlor dauerhaft den Zugriff auf sein eigenes (bezahltes) Konto, sobald
  seine Session ablief. Kein Zeitfenster-Zufall, sondern jederzeit vom
  Angreifer aktiv ausloesbar.

  Fix: `user_directory` wird jetzt IMMER beim Provisionieren belegt, auch
  ohne Passwort -- die E-Mail gehoert ab dem ersten Anlegen "ihrem" Mandanten,
  ein Angreifer kann sie nicht mehr fuer einen eigenen Mandanten kapern.
  Das bedeutet umgekehrt, dass `/v1/auth/signup` fuer eine SOLCHE E-Mail jetzt
  auf den (schon vorhandenen, aber passwortlosen) `user_directory`-Eintrag
  trifft -- siehe `_claim_existing_account` in `app/routes/auth.py`: der
  ECHTE Eigentuemer setzt darueber sein erstes Passwort auf dem BESTEHENDEN
  Nutzer ("Konto beanspruchen"), statt einen neuen Mandanten zu bekommen.
  Verbleibendes Restrisiko (keine E-Mail-Verifikation in dieser Umgebung,
  siehe README): wer zuerst nach dem Kauf ein Passwort beansprucht, gewinnt.
"""
from __future__ import annotations

import psycopg
from fastapi import HTTPException

from .auth import hash_password
from .db import admin_tx


def _provision_in(
    conn, tenant_name: str, owner_email: str, plan_code: str, password: str | None
) -> dict:
    plan = conn.execute("SELECT id FROM plans WHERE code = %s", (plan_code,)).fetchone()
    if plan is None:
        raise HTTPException(status_code=400, detail=f"Tarif '{plan_code}' unbekannt")

    tenant_id = conn.execute(
        "INSERT INTO tenants (name, plan_id) VALUES (%s, %s) RETURNING id",
        (tenant_name, plan["id"]),
    ).fetchone()["id"]

    # users ist RLS-geschuetzt; Mandantenkontext setzen, damit der INSERT die
    # WITH CHECK-Policy erfuellt. is_local=true gilt fuer den Rest DIESER
    # Transaktion -- ruft ein Aufrufer (z.B. der Stripe-Webhook in
    # app/routes/billing.py) mit einer eigenen offenen `conn` auf, bleibt der
    # Kontext auch fuer dessen NACHFOLGENDE Statements (z.B. die Session
    # anlegen) in derselben Transaktion gesetzt.
    conn.execute("SELECT set_config('app.current_tenant', %s, true)", (str(tenant_id),))
    password_hash = hash_password(password) if password else None
    user_id = conn.execute(
        "INSERT INTO users (tenant_id, email, role, password_hash) "
        "VALUES (%s, %s, 'owner', %s) RETURNING id",
        (tenant_id, owner_email, password_hash),
    ).fetchone()["id"]

    # Sicherheits-Fix: IMMER sofort reservieren, auch ohne Passwort (siehe
    # Modul-Docstring) -- schliesst das Uebernahme-Zeitfenster fuer
    # passwortlos provisionierte Nutzer (Stripe/Shopify) vollstaendig.
    try:
        conn.execute(
            "INSERT INTO user_directory (email_lower, tenant_id, user_id) "
            "VALUES (%s, %s, %s)",
            (owner_email.lower(), tenant_id, user_id),
        )
    except psycopg.errors.UniqueViolation as exc:
        # Rollback der gesamten Transaktion (inkl. gerade angelegtem
        # Mandanten) -- kein verwaister Mandant bei doppelter E-Mail.
        raise HTTPException(
            status_code=409, detail="Diese E-Mail-Adresse ist bereits registriert"
        ) from exc

    return {
        "tenant_id": str(tenant_id),
        "user_id": str(user_id),
        "plan": plan_code,
    }


def provision_tenant(
    tenant_name: str,
    owner_email: str,
    plan_code: str,
    password: str | None = None,
    conn=None,
) -> dict:
    """Legt Mandant + Owner-Nutzer an und reserviert die E-Mail SOFORT in
    `user_directory` -- MIT oder OHNE `password` (Sicherheits-Fix, siehe
    Modul-Docstring). Ohne `password` bleibt der Nutzer selbst ohne Passwort
    (kein Login-Weg, bis eines gesetzt wird -- entweder ueber
    `_claim_existing_account` in `app/routes/auth.py` oder eine anderweitig
    erzeugte Session, siehe `app/routes/billing.py`); mit `password` kann
    sich der Nutzer sofort per `/v1/auth/login` anmelden.

    `conn`: optionale bestehende Transaktion. Webhooks uebergeben ihre
    Transaktion, damit Idempotenz-Belegung und Anlage EIN Commit sind.
    """
    if conn is not None:
        return _provision_in(conn, tenant_name, owner_email, plan_code, password)
    with admin_tx() as c:
        return _provision_in(c, tenant_name, owner_email, plan_code, password)
