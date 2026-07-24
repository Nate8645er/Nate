"""Laufzeit-Beweis der DB-erzwungenen Mandantentrennung.

Laeuft nur, wenn eine Postgres-Testdatenbank bereitsteht (Umgebungsvariable
PLATFORM_TEST_DATABASE_URL = privilegierte/Superuser-Verbindung). Sonst wird
der Test uebersprungen (z.B. in der reinen Unit-Umgebung ohne DB).

Der Test:
  1. migriert das Schema (legt Tabellen + Rolle app_rw + Grants an),
  2. gibt app_rw ein LOGIN-Passwort,
  3. legt zwei Mandanten mit je einem usage_events-Datensatz an,
  4. verbindet sich ALS app_rw (RLS-gebunden) und beweist:
     - mit Kontext A sieht man nur A,
     - mit Kontext B sieht man nur B,
     - ohne Kontext sieht man NICHTS.
"""
from __future__ import annotations

import os

import pytest

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


@pytest.fixture()
def seeded():
    import psycopg

    # settings direkt setzen (robust gegen Import-Reihenfolge: config liest die
    # Umgebung nur einmal beim Import, andere Testmodule koennen sie vorher mit
    # Dummy-Werten geladen haben).
    from app.config import settings

    settings.migrate_database_url = DSN
    from app.db import migrate

    migrate()

    with psycopg.connect(DSN, autocommit=True) as conn:
        # app_rw ein bekanntes Login-Passwort geben (Test-DB, lokal/CI).
        conn.execute("ALTER ROLE app_rw LOGIN PASSWORD 'app_rw_test'")

        # Zwei Mandanten auf dem Free-Tarif anlegen.
        plan = conn.execute("SELECT id FROM plans WHERE code='free'").fetchone()[0]
        a = conn.execute(
            "INSERT INTO tenants (name, plan_id) VALUES ('A', %s) RETURNING id",
            (plan,),
        ).fetchone()[0]
        b = conn.execute(
            "INSERT INTO tenants (name, plan_id) VALUES ('B', %s) RETURNING id",
            (plan,),
        ).fetchone()[0]
        for t in (a, b):
            conn.execute(
                "INSERT INTO usage_events (tenant_id, model, tokens_in, tokens_out) "
                "VALUES (%s,'ollama/llama3.2',10,20)",
                (t,),
            )
    # app_rw-Verbindungs-DSN aus der Admin-DSN ableiten.
    import urllib.parse as up

    p = up.urlparse(DSN)
    app_dsn = f"postgresql://app_rw:app_rw_test@{p.hostname}:{p.port or 5432}{p.path}"
    return str(a), str(b), app_dsn


def _count_as_app(app_dsn: str, tenant_id: str | None) -> int:
    import psycopg

    with psycopg.connect(app_dsn) as conn:
        with conn.transaction():
            if tenant_id is not None:
                conn.execute(
                    "SELECT set_config('app.current_tenant', %s, true)", (tenant_id,)
                )
            return conn.execute("SELECT count(*) FROM usage_events").fetchone()[0]


def test_tenant_context_isolates_rows(seeded):
    a, b, app_dsn = seeded
    # Genau eine Zeile je Mandant im aktuellen Monat.
    assert _count_as_app(app_dsn, a) == 1
    assert _count_as_app(app_dsn, b) == 1


def test_without_context_sees_nothing(seeded):
    _a, _b, app_dsn = seeded
    # Kein Kontext -> current_tenant() ist NULL -> RLS blockt alles.
    assert _count_as_app(app_dsn, None) == 0
