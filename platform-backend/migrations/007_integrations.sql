-- Integrationen (Slack/Notion/Google) pro Mandant (mandantengebunden via RLS).
-- Anzahl ist tarifgebunden (plans.max_integrations) und wird beim Anlegen in
-- der Anwendung durchgesetzt. ACHTUNG: dies ist ein Geruest ohne echten
-- OAuth-Flow -- status bleibt beim Anlegen immer 'disconnected'
-- (siehe app/routes/integrations.py).

BEGIN;

CREATE TABLE IF NOT EXISTS integrations (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id  uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    provider   text NOT NULL CHECK (provider IN ('slack', 'notion', 'google')),
    status     text NOT NULL DEFAULT 'disconnected' CHECK (status IN ('disconnected', 'connected')),
    config     jsonb NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE integrations FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON integrations;
CREATE POLICY tenant_isolation ON integrations
    USING (tenant_id = current_tenant())
    WITH CHECK (tenant_id = current_tenant());

-- Anders als bei billing_events braucht die App hier auch DELETE (Mandant
-- kann eine Integration selbst wieder entfernen).
GRANT SELECT, INSERT, UPDATE, DELETE ON integrations TO app_rw;

COMMIT;
