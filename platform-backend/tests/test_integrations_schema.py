"""Struktur-Test der Integrations-Migration (ohne DB)."""
import pathlib

MIG = (
    pathlib.Path(__file__).resolve().parent.parent
    / "migrations"
    / "007_integrations.sql"
).read_text(encoding="utf-8")


def test_integrations_is_rls_protected():
    assert "ENABLE ROW LEVEL SECURITY" in MIG
    assert "FORCE ROW LEVEL SECURITY" in MIG
    assert "DROP POLICY IF EXISTS tenant_isolation ON integrations" in MIG
    assert "tenant_id = current_tenant()" in MIG


def test_integrations_granted_to_app_rw():
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON integrations TO app_rw" in MIG


def test_integrations_provider_and_status_checked():
    assert "CHECK (provider IN ('slack', 'notion', 'google'))" in MIG
    assert "CHECK (status IN ('disconnected', 'connected'))" in MIG
    assert "DEFAULT 'disconnected'" in MIG
