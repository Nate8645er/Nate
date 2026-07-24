-- Laufzeit-Rolle app_rw: NOSUPERUSER, NOBYPASSRLS, NICHT Tabellen-Owner.
-- Nur fuer diese Art Rolle wird RLS wirksam erzwungen (Superuser/BYPASSRLS
-- umgehen RLS auch bei FORCE). Die App verbindet sich ausschliesslich als
-- app_rw; Migrationen laufen mit einer privilegierten Rolle (MIGRATE_DATABASE_URL).
--
-- Portabel & idempotent: Existiert app_rw bereits (z. B. von einem
-- docker-entrypoint-initdb.d-Skript mit LOGIN+Passwort oder auf einer
-- gemanagten DB), wird nichts geaendert. Sonst wird eine NOLOGIN-Rolle
-- angelegt; Login/Passwort vergibt die Infrastruktur (siehe README).

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_rw') THEN
        CREATE ROLE app_rw NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
    END IF;
END $$;
