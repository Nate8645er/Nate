#!/bin/bash
# Startet den Token-Savior-MCP-Server; installiert ihn vorher bei Bedarf.
# Wird von .mcp.json referenziert (Server "token-savior").
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$DIR/ensure-install.sh" || {
  echo "token-savior: Installation fehlgeschlagen" >&2
  exit 1
}
exec "$HOME/.local/token-savior-venv/bin/token-savior" "$@"
