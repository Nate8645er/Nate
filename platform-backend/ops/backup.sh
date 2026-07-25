#!/bin/bash
# Sichert die Datenbank per pg_dump (Custom-Format, komprimiert, fuer
# schnelles selektives Restore geeignet). Braucht DATABASE_URL_ADMIN mit
# ausreichenden Rechten (mind. Lesezugriff auf alle Tabellen -> die
# Migrations-Rolle, NICHT app_rw, da app_rw durch RLS nur den eigenen
# Mandantenkontext saehe).
#
# Nutzung:
#   DATABASE_URL_ADMIN=postgresql://postgres:...@host:5432/platform \
#     ops/backup.sh [ziel-verzeichnis]
set -euo pipefail

: "${DATABASE_URL_ADMIN:?DATABASE_URL_ADMIN fehlt (privilegierte Verbindung fuer den Dump)}"

OUT_DIR="${1:-./backups}"
mkdir -p "$OUT_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="$OUT_DIR/platform_${STAMP}.dump"

# schema_migrations bewusst ausschliessen: --no-privileges streicht GRANTs
# aus dem Dump (Rollen/Rechte sollen im Ziel-Cluster ohnehin vorhanden sein,
# siehe db-init/ + Migrationen). Kaeme schema_migrations mit zurueck, wuerde
# `migrate()` nach dem Restore denken "alles schon angewendet" und die
# gestrichenen GRANTs NICHT erneut setzen. Ohne die Tabelle laeuft migrate()
# nach dem Restore vollstaendig neu — sicher, weil jede Migration idempotent
# ist (IF NOT EXISTS / DROP POLICY IF EXISTS / ON CONFLICT DO UPDATE).
pg_dump --format=custom --no-owner --no-privileges \
  --exclude-table=schema_migrations \
  --dbname="$DATABASE_URL_ADMIN" --file="$FILE"

echo "Backup geschrieben: $FILE"
