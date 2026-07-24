-- Agenten pro Mandant (mandantengebunden via RLS). Anzahl ist tarifgebunden
-- (plans.max_agents) und wird beim Anlegen in der Anwendung durchgesetzt.

BEGIN;

CREATE TABLE IF NOT EXISTS agents (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name          text NOT NULL,
    system_prompt text NOT NULL DEFAULT '',
    model         text NOT NULL,
    created_at    timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON agents;
CREATE POLICY tenant_isolation ON agents
    USING (tenant_id = current_tenant())
    WITH CHECK (tenant_id = current_tenant());

GRANT SELECT, INSERT, UPDATE, DELETE ON agents TO app_rw;

COMMIT;
