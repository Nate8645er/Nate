"""Struktur-Test der Agenten-Migration (ohne DB)."""
import pathlib

MIG = (
    pathlib.Path(__file__).resolve().parent.parent / "migrations" / "004_agents.sql"
).read_text(encoding="utf-8")


def test_agents_is_rls_protected():
    assert "ENABLE ROW LEVEL SECURITY" in MIG
    assert "FORCE ROW LEVEL SECURITY" in MIG
    assert "DROP POLICY IF EXISTS tenant_isolation ON agents" in MIG
    assert "tenant_id = current_tenant()" in MIG


def test_agents_granted_to_app_rw():
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON agents TO app_rw" in MIG
