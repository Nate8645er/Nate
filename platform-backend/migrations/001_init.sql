-- Produkt A — Fundament: Multi-Tenant-Schema mit erzwungener Mandantentrennung.
-- Mandantentrennung geschieht auf DB-Ebene via Row Level Security (RLS),
-- nicht nur in der Anwendungslogik (Definition of Done, Master-Prompt 3.4).
--
-- Die Anwendung setzt pro Request `SET LOCAL app.current_tenant = '<uuid>'`.
-- Alle mandantengebundenen Tabellen filtern darueber. Ein Bug in der
-- Anwendung kann so keine fremden Zeilen zurueckgeben.

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- gen_random_uuid()

-- ---------------------------------------------------------------------------
-- Tarife (nicht mandantengebunden — globaler Katalog, Master-Prompt 3.3)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plans (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code                 text NOT NULL UNIQUE,          -- free | starter | pro | business | enterprise
    name                 text NOT NULL,
    price_chf_cents      integer NOT NULL DEFAULT 0,    -- CHF inkl. MwSt, in Rappen
    allowed_models       jsonb NOT NULL DEFAULT '[]',   -- ["anthropic/claude-...","ollama/llama3", ...]
    max_agents           integer NOT NULL DEFAULT 1,
    monthly_token_limit  bigint  NOT NULL DEFAULT 100000, -- harte Obergrenze pro Kalendermonat
    max_integrations     integer NOT NULL DEFAULT 0,
    features             jsonb   NOT NULL DEFAULT '{}',
    created_at           timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Mandanten
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tenants (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text NOT NULL,
    plan_id     uuid NOT NULL REFERENCES plans(id),
    status      text NOT NULL DEFAULT 'active'          -- active | suspended | cancelled
                CHECK (status IN ('active','suspended','cancelled')),
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Nutzer (mandantengebunden)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email       text NOT NULL,
    role        text NOT NULL DEFAULT 'member'          -- owner | admin | member
                CHECK (role IN ('owner','admin','member')),
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, email)
);

-- ---------------------------------------------------------------------------
-- API-Schluessel (mandantengebunden). Es wird NUR der SHA-256-Hash gespeichert.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS api_keys (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key_hash    text NOT NULL UNIQUE,                   -- sha256(hex) des Klartext-Keys
    label       text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    last_used_at timestamptz
);

-- ---------------------------------------------------------------------------
-- Konversationen + Nachrichten (mandantengebunden)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id     uuid REFERENCES users(id) ON DELETE SET NULL,
    title       text NOT NULL DEFAULT 'Neue Unterhaltung',
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            text NOT NULL CHECK (role IN ('system','user','assistant')),
    content         text NOT NULL,
    model           text,
    tokens_in       integer NOT NULL DEFAULT 0,
    tokens_out      integer NOT NULL DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Verbrauchsereignisse (mandantengebunden) — Grundlage der Abrechnung
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usage_events (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    ts          timestamptz NOT NULL DEFAULT now(),
    model       text NOT NULL,
    tokens_in   integer NOT NULL DEFAULT 0,
    tokens_out  integer NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_usage_tenant_ts ON usage_events (tenant_id, ts);
CREATE INDEX IF NOT EXISTS idx_messages_conv   ON messages (conversation_id);

-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------
-- Helper: aktueller Mandant aus der Session-Variable. STABLE, damit planbar.
CREATE OR REPLACE FUNCTION current_tenant() RETURNS uuid
LANGUAGE sql STABLE AS $$
    SELECT nullif(current_setting('app.current_tenant', true), '')::uuid
$$;

-- Wichtig zur Rollen-Architektur (siehe 003_grants.sql + docker-compose.yml):
-- Die Laufzeit verbindet sich mit der Rolle app_rw (NOSUPERUSER, NOBYPASSRLS,
-- NICHT Tabellen-Owner). Fuer eine solche Rolle greift die normale RLS immer.
-- FORCE zusaetzlich, damit die Isolation auch dann haelt, falls der Owner in
-- Produktion einmal keine Superuser-Rolle ist.
--
-- api_keys ist bewusst NICHT in dieser Schleife: der Auth-Lookup erfolgt ueber
-- den global-eindeutigen, geheimen key_hash (SHA-256 von 256-Bit-Zufall). Man
-- findet eine Zeile nur, wenn man das Geheimnis bereits kennt — es gibt keine
-- mandantenuebergreifende Aufzaehlung. Wuerde api_keys unter RLS stehen, koennte
-- der kontextlose Login-Lookup keine Zeile sehen (Henne-Ei: der Mandant wird
-- ERST durch diesen Lookup bestimmt).
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['users','conversations','messages','usage_events']
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I', t);  -- idempotent
        EXECUTE format($p$
            CREATE POLICY tenant_isolation ON %I
            USING (tenant_id = current_tenant())
            WITH CHECK (tenant_id = current_tenant())
        $p$, t);
    END LOOP;
END $$;

COMMIT;
