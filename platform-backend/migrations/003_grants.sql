-- Minimale Rechte fuer die Laufzeit-Rolle app_rw. Kein DDL, kein Ownership.
-- app_rw ist damit vollstaendig der RLS unterworfen (Mandantentrennung greift).

GRANT USAGE ON SCHEMA public TO app_rw;

-- Globale Kataloge (keine RLS): lesen; tenants zusaetzlich anlegen (Provision).
GRANT SELECT ON plans   TO app_rw;
GRANT SELECT, INSERT, UPDATE ON tenants TO app_rw;

-- api_keys (keine RLS, geheimer key_hash): lesen/anlegen/last_used aktualisieren.
GRANT SELECT, INSERT, UPDATE ON api_keys TO app_rw;

-- Mandantengebundene Tabellen (RLS erzwingt die Trennung trotz voller DML-Rechte).
GRANT SELECT, INSERT, UPDATE, DELETE ON users         TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON conversations TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON messages      TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON usage_events  TO app_rw;
