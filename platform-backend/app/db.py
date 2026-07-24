"""Datenbank-Zugriff mit erzwungener Mandantentrennung.

Kernidee: Vor jeder mandantengebundenen Abfrage wird
`SET LOCAL app.current_tenant = '<uuid>'` gesetzt. Die RLS-Policies aus
001_init.sql filtern dann automatisch auf diesen Mandanten. `SET LOCAL`
gilt nur bis zum Transaktionsende — es kann also nicht in eine andere
Anfrage "durchsickern".

Die Laufzeit-Verbindung nutzt die Rolle app_rw (NOSUPERUSER, NOBYPASSRLS,
nicht Owner) — nur so wird RLS wirklich erzwungen. Migrationen laufen ueber
eine separate, privilegierte Verbindung (MIGRATE_DATABASE_URL).
"""
from __future__ import annotations

import contextlib
from collections.abc import Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import settings

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=10,
            # autocommit=False ist psycopg3-Default; explizit, weil die
            # is_local=true-Semantik von SET LOCAL genau davon abhaengt.
            kwargs={"row_factory": dict_row, "autocommit": False},
            open=True,
        )
    return _pool


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextlib.contextmanager
def admin_tx() -> Iterator[psycopg.Connection]:
    """Transaktion OHNE Mandantenkontext — nur fuer nicht-RLS-Tabellen
    (plans, tenants, api_keys)."""
    with get_pool().connection() as conn:
        with conn.transaction():
            yield conn


@contextlib.contextmanager
def tenant_tx(tenant_id: str) -> Iterator[psycopg.Connection]:
    """Transaktion MIT gesetztem Mandantenkontext. Alle RLS-geschuetzten
    Tabellen sind dadurch automatisch auf diesen Mandanten begrenzt."""
    with get_pool().connection() as conn:
        with conn.transaction():
            # Parametrisiert via set_config, damit keine SQL-Injection ueber die
            # tenant_id moeglich ist. is_local=true -> gilt nur in dieser Tx.
            conn.execute(
                "SELECT set_config('app.current_tenant', %s, true)", (tenant_id,)
            )
            yield conn


def migrate() -> None:
    """Wendet die SQL-Dateien in migrations/ genau einmal an (Tracking-Tabelle
    schema_migrations). Laeuft ueber die privilegierte Migrations-Verbindung."""
    import pathlib

    mig_dir = pathlib.Path(__file__).resolve().parent.parent / "migrations"
    files = sorted(mig_dir.glob("*.sql"))

    with psycopg.connect(settings.migrate_database_url) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " filename text PRIMARY KEY,"
            " applied_at timestamptz NOT NULL DEFAULT now())"
        )
        conn.commit()
        applied = {
            r[0]
            for r in conn.execute("SELECT filename FROM schema_migrations").fetchall()
        }
        for f in files:
            if f.name in applied:
                continue
            conn.execute(f.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)", (f.name,)
            )
            conn.commit()
