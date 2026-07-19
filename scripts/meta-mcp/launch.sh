#!/bin/bash
# Startet den meta-mcp-Server (Meta Ads, HTTP auf Port 3000) bei Bedarf und
# verbindet Claude Code per stdio<->HTTP-Bridge (mcp-remote).
# Wird von .mcp.json referenziert (Server "meta-mcp").
#
# Zugangsdaten liegen in meta-mcp/.env (gitignored):
#   META_ACCESS_TOKEN  - Meta System-User-Token (ads_management, ads_read)
#   META_AD_ACCOUNT_ID - z.B. act_123456789
#   MCP_API_KEY        - wird hier automatisch generiert, schuetzt den Port
set -u
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP="$DIR/meta-mcp"
ENVFILE="$APP/.env"
PORT="${META_MCP_PORT:-3000}"

# .env anlegen, falls fehlend (mit generiertem API-Key und Token-Platzhalter)
if [ ! -f "$ENVFILE" ]; then
  KEY=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')
  {
    echo "MCP_API_KEY=$KEY"
    echo "# Meta-Zugangsdaten eintragen (siehe scripts/meta-mcp/SETUP-NOTES.md):"
    echo "#META_ACCESS_TOKEN="
    echo "#META_AD_ACCOUNT_ID=act_"
    echo "PORT=$PORT"
  } > "$ENVFILE"
fi
API_KEY=$(grep -E '^MCP_API_KEY=' "$ENVFILE" | head -1 | cut -d= -f2-)

# Abhaengigkeiten/Build sicherstellen (Container sind ephemer)
if [ ! -f "$APP/dist/index.js" ]; then
  (cd "$APP" && npm install --silent > /dev/null 2>&1 && npm run build > /dev/null 2>&1) || {
    echo "meta-mcp: Build fehlgeschlagen" >&2; exit 1; }
fi

# Server starten, falls er nicht laeuft
if ! curl -sf --noproxy '*' "http://127.0.0.1:$PORT/health" > /dev/null 2>&1; then
  (cd "$APP" && nohup node dist/index.js >> "$APP/server.log" 2>&1 &)
  for _ in $(seq 1 30); do
    curl -sf --noproxy '*' "http://127.0.0.1:$PORT/health" > /dev/null 2>&1 && break
    sleep 0.5
  done
fi

# stdio-Bridge zum lokalen HTTP-Endpoint
exec npx -y mcp-remote "http://127.0.0.1:$PORT/mcp" \
  --header "Authorization: Bearer $API_KEY" \
  --allow-http
