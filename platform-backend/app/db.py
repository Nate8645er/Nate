"""Datenbank-Zugriff mit erzwungener Mandantentrennung.

Kernidee: Vor jeder mandantengebundenen Abfrage wird
`SET LOCAL app.current_tenant = '<uuid>'` gesetzt. Die RLS-Policies aus
001_init.sql filtern dann automatisch auf diesen Mandanten. `SET LOCAL`
gilt nur bis zum Transaktionsende — es kann also nicht in eine andere
Anfrage "durchsickern".
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
            kwargs={"row_factory": dict_row},
            open=True,
        )
    return _pool


@contextlib.contextmanager
def admin_tx() -> Iterator[psycopg.Connection]:
    """Transaktion OHNE Mandantenkontext — nur fuer nicht-mandantengebundene
    Tabellen (plans, tenants, api_keys-Lookup beim Login)."""
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
    """Wendet die SQL-Dateien in migrations/ der Reihe nach an (idempotent)."""
    import pathlib

    mig_dir = pathlib.Path(__file__).resolve().parent.parent / "migrations"
    files = sorted(mig_dir.glob("*.sql"))
    with get_pool().connection() as conn:
        for f in files:
            conn.execute(f.read_text(encoding="utf-8"))
        conn.commit()
