#!/usr/bin/env bash
# Backup of the persistent state (encrypted key, loss ledger, positions, users,
# audit log). The Coinbase key stays ENCRYPTED in the backup too. Keep backups
# off the server as well if you can.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$HERE/backups/state-$STAMP.tar.gz"
mkdir -p "$HERE/backups"
tar -czf "$OUT" -C "$HERE" state
# keep the 14 most recent
ls -1t "$HERE"/backups/state-*.tar.gz | tail -n +15 | xargs -r rm -f
echo "Backup: $OUT"
