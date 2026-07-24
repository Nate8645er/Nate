#!/bin/bash
# Laeuft einmalig beim ersten Init des Postgres-Containers (leeres pgdata).
# Legt die eingeschraenkte Laufzeit-Rolle app_rw mit LOGIN + Passwort an.
# RLS wirkt nur fuer eine solche Rolle (NOSUPERUSER, NOBYPASSRLS).
# Grants auf die Tabellen erfolgen spaeter in Migration 003 (Tabellen muessen
# erst existieren).
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_rw') THEN
            CREATE ROLE app_rw LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE
                PASSWORD '${APP_DB_PASSWORD}';
        END IF;
    END
    \$\$;
EOSQL
