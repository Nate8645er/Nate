#!/bin/bash
# Stellt einen mit backup.sh erstellten Dump in eine (leere) Ziel-Datenbank
# wieder her. Fuer eine Wiederherstellungsprobe gegen eine FRISCHE, temporaere
# Datenbank ausfuehren — niemals ungeprueft gegen Produktion.
#
# Nutzung:
#   DATABASE_URL_ADMIN=postgresql://postgres:...@host:5432/restore_target \
#     ops/restore.sh backups/platform_20260101T000000Z.dump
set -euo pipefail

: "${DATABASE_URL_ADMIN:?DATABASE_URL_ADMIN fehlt (Ziel-Datenbank fuer den Restore)}"
DUMP_FILE="${1:?Nutzung: restore.sh <dump-datei>}"

pg_restore --no-owner --no-privileges --clean --if-exists \
  --dbname="$DATABASE_URL_ADMIN" "$DUMP_FILE"

echo "Restore abgeschlossen aus: $DUMP_FILE"
echo "Naechster Schritt (Pflicht): Rollen/Grants wiederherstellen —"
echo "  MIGRATE_DATABASE_URL=\$DATABASE_URL_ADMIN DATABASE_URL=<app_rw-Verbindung> python -m app.migrate"
echo "(schema_migrations ist nicht im Dump enthalten -> migrate() laeuft"
echo " vollstaendig und idempotent neu, das setzt die GRANTs korrekt neu.)"
