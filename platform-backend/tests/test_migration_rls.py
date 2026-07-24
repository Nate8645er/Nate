"""Struktur-Test des Schemas (ohne laufende DB). Der echte Laufzeit-Beweis
der Mandantentrennung steht in test_rls_integration.py."""
import pathlib

MIG = (
    pathlib.Path(__file__).resolve().parent.parent
    / "migrations"
    / "001_init.sql"
).read_text(encoding="utf-8")

# api_keys ist bewusst NICHT RLS-gebunden (Lookup ueber geheimen key_hash).
TENANT_TABLES = ["users", "conversations", "messages", "usage_events"]


def test_rls_and_force_present():
    assert "ENABLE ROW LEVEL SECURITY" in MIG
    assert "FORCE ROW LEVEL SECURITY" in MIG


def test_policy_uses_current_tenant():
    assert "current_tenant()" in MIG
    assert "tenant_id = current_tenant()" in MIG


def test_policy_is_idempotent():
    # Neustart gegen persistiertes Volume darf nicht an "policy already exists"
    # scheitern.
    assert "DROP POLICY IF EXISTS tenant_isolation" in MIG


def test_all_tenant_tables_listed_for_rls():
    for t in TENANT_TABLES:
        assert f"'{t}'" in MIG, f"{t} fehlt in der RLS-Schleife"


def test_api_keys_not_in_rls_loop():
    # Die FOREACH-Schleife darf api_keys nicht enthalten (sonst bricht der
    # kontextlose Auth-Lookup).
    loop = MIG.split("FOREACH t IN ARRAY ARRAY[")[1].split("]")[0]
    assert "'api_keys'" not in loop
