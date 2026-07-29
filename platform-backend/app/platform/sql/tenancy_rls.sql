-- Mandantentrennung auf DB-Ebene (Postgres Row-Level-Security).
-- Einmal je Umgebung ausführen. Danach liefert die DB selbst bei Code-Fehlern
-- nur Zeilen des in der Session gesetzten Tenants.
-- Voraussetzung: die Anwendung setzt pro Request
--   SELECT set_config('app.current_tenant', '<tenant>', true);

ALTER TABLE tenant_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_records FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON tenant_records;
CREATE POLICY tenant_isolation ON tenant_records
  USING (tenant_id = current_setting('app.current_tenant', true))
  WITH CHECK (tenant_id = current_setting('app.current_tenant', true));

ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS audit_tenant_isolation ON audit_events;
CREATE POLICY audit_tenant_isolation ON audit_events
  USING (tenant_id = current_setting('app.current_tenant', true))
  WITH CHECK (tenant_id = current_setting('app.current_tenant', true));

-- Audit ist append-only: kein UPDATE/DELETE für die Anwendungsrolle.
-- (Rechte-Vergabe hier bewusst als Kommentar — Rollennamen umgebungsabhängig.)
-- REVOKE UPDATE, DELETE ON audit_events FROM app_role;
