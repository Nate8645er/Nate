"""Struktur-Test: das Schema erzwingt RLS auf allen mandantengebundenen
Tabellen. Verifiziert die Definition of Done ("RLS, nicht nur App-Logik")
ohne laufende DB, durch Pruefung der Migrationsdatei."""
import pathlib

MIG = (
    pathlib.Path(__file__).resolve().parent.parent
    / "migrations"
    / "001_init.sql"
).read_text(encoding="utf-8")

TENANT_TABLES = ["users", "api_keys", "conversations", "messages", "usage_events"]


def test_rls_and_force_present():
    assert "ENABLE ROW LEVEL SECURITY" in MIG
    assert "FORCE ROW LEVEL SECURITY" in MIG  # gilt auch fuer den Tabellen-Owner


def test_policy_uses_current_tenant():
    assert "current_tenant()" in MIG
    assert "tenant_id = current_tenant()" in MIG


def test_all_tenant_tables_listed_for_rls():
    # Die Migration iteriert ueber genau diese Tabellen im FOREACH-Array.
    for t in TENANT_TABLES:
        assert f"'{t}'" in MIG, f"{t} fehlt in der RLS-Schleife"
