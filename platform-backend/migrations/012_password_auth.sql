-- Web-Login mit E-Mail+Passwort statt rohem API-Schluessel im Chat-UI --
-- bisher musste sich ein Kunde einen `pk_...`-Key einfuegen (siehe
-- static/index.html), ganz anders als bei ChatGPT/Claude/Kimi. Ausserdem gab
-- es ueberhaupt keinen Weg, sich selbst fuer den Free-Tarif anzumelden --
-- nur `/admin/provision` (admin-token-geschuetzt) und die Stripe/Shopify-
-- Webhooks konnten `provision_tenant()` aufrufen. Das widersprach der
-- Store-FAQ ("Free-Tarif dauerhaft kostenlos, keine Kreditkarte noetig").
--
-- Diese Migration legt das Fundament fuer `/v1/auth/signup|login|logout`
-- (app/routes/auth.py):
--   1. users.password_hash  -- bcrypt-Hash, NULLABLE (bestehende, ueber
--      /admin/provision oder Webhooks angelegte Zeilen haben kein Passwort
--      und bleiben weiter ueber Bearer-API-Key nutzbar).
--   2. user_directory        -- E-Mail -> Mandant/Nutzer, GLOBAL eindeutig.
--   3. sessions               -- Web-Login-Sitzungen, nur der Hash des
--      Cookie-Tokens wird gespeichert (nie der Klartext).

BEGIN;

-- ---------------------------------------------------------------------------
-- 1) Passwort-Hash auf dem bestehenden Nutzer. Bleibt RLS-gebunden wie bisher
--    (siehe 001_init.sql) -- WICHTIG: dieses Feld absichtlich NICHT von RLS
--    ausnehmen, weil app/billing.py::resolve_metadata_tenant sich beim
--    Stripe-Metadaten-Haerten (Security-Review HOCH-1) genau auf die
--    RLS-Filterung von `users` verlaesst ("gehoert diese E-Mail zu GENAU
--    diesem Mandanten"). Wuerde man RLS hier abschalten (wie bei api_keys),
--    wuerde diese Eigentumspruefung wirkungslos -- ein Angreifer koennte mit
--    einer beliebigen bekannten E-Mail jeden Mandanten per Checkout-Metadaten
--    kapern. Siehe app/billing.py Zeile ~153.
-- ---------------------------------------------------------------------------
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash text;

-- ---------------------------------------------------------------------------
-- 2) E-Mail-Verzeichnis: loest genau das Henne-Ei-Problem, das auch
--    api_keys hat (der Mandant ist beim Login noch unbekannt, RLS kann also
--    fuer DIESEN einen Lookup-Schritt nicht greifen -- siehe require_principal
--    in app/auth.py und der Kommentar dort zu api_keys).
--
--    Anders als api_keys speichert diese Tabelle ABSICHTLICH kein Geheimnis
--    (kein Passwort-Hash) -- nur die Zuordnung E-Mail -> (tenant_id, user_id).
--    Damit bleibt der eigentliche Passwort-Hash weiter unter RLS in `users`
--    (siehe Kommentar oben); der Login-Ablauf ist zweistufig:
--      a) admin_tx()  : user_directory nach E-Mail durchsuchen (kein RLS,
--                       liefert nur tenant_id + user_id, kein Geheimnis).
--      b) tenant_tx() : mit dem so gefundenen tenant_id ganz normal
--                       (RLS-konform) den password_hash aus `users` lesen.
--
--    GLOBAL eindeutig (PRIMARY KEY auf email_lower) -- pro Sitzung mit
--    Passwort-Login genau ein Nutzer/Mandant. Bereits ohne Passwort
--    angelegte users-Zeilen (Admin/Webhook-Provisionierung) tauchen hier
--    NICHT auf, bis der Nutzer sich einmal per Self-Service-Signup
--    registriert -- diese Zeilen bleiben dem Bearer-Token-Pfad vorbehalten.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_directory (
    email_lower text PRIMARY KEY,
    tenant_id    uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   timestamptz NOT NULL DEFAULT now()
);
GRANT SELECT, INSERT, DELETE ON user_directory TO app_rw;

-- ---------------------------------------------------------------------------
-- 3) Web-Sitzungen (HttpOnly-Cookie). Wie api_keys: nur der SHA-256-Hash
--    eines hochentropischen Zufallstokens (secrets.token_urlsafe(32), 256
--    Bit) wird gespeichert -- ein Fund in dieser Tabelle setzt bereits
--    Kenntnis des Geheimnisses voraus, RLS-Ausnahme ist hier also aus
--    demselben Grund vertretbar wie bei api_keys (siehe 001_init.sql).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash    text NOT NULL UNIQUE,
    tenant_id     uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id       uuid REFERENCES users(id) ON DELETE CASCADE,
    created_at    timestamptz NOT NULL DEFAULT now(),
    expires_at    timestamptz NOT NULL,
    last_used_at  timestamptz
);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions (expires_at);
GRANT SELECT, INSERT, UPDATE, DELETE ON sessions TO app_rw;

COMMIT;
