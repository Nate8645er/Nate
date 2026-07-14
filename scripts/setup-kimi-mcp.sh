#!/usr/bin/env bash
# Setup für die Kimi-Code-MCP-Integration (kimi-mcp-server, vendored unter tools/kimi-code-mcp).
# Baut den MCP-Server, installiert optional die Kimi-CLI und prüft die Konfiguration.
# Idempotent — kann beliebig oft ausgeführt werden (z. B. als SessionStart-Hook).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_DIR="$REPO_ROOT/tools/kimi-code-mcp"

echo "==> Kimi-Code-MCP-Setup"

command -v node >/dev/null || { echo "FEHLER: Node.js >= 18 wird benötigt."; exit 1; }
command -v npm  >/dev/null || { echo "FEHLER: npm wird benötigt."; exit 1; }

echo "==> Baue MCP-Server ($MCP_DIR)"
cd "$MCP_DIR"
npm install --no-fund --no-audit
npm run build

echo "==> Globale Claude-Code-Konfiguration (~/.claude/mcp.json)"
mkdir -p "$HOME/.claude"
cat > "$HOME/.claude/mcp.json" <<EOF
{
  "mcpServers": {
    "kimi-code": {
      "command": "node",
      "args": ["$MCP_DIR/dist/index.js"]
    }
  }
}
EOF

# Kimi-CLI (nur für kimi_analyze / kimi_resume nötig; API-Tools brauchen sie nicht)
if ! command -v kimi >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/kimi" ]; then
  if command -v uv >/dev/null 2>&1; then
    echo "==> Installiere Kimi-CLI via uv (optional, für kimi_analyze/kimi_resume)"
    uv tool install kimi-cli || echo "WARNUNG: Kimi-CLI-Installation fehlgeschlagen (nicht kritisch)."
  else
    echo "HINWEIS: 'uv' nicht gefunden — Kimi-CLI übersprungen (nur für kimi_analyze nötig)."
  fi
fi

echo "==> Prüfe API-Key"
if [ -n "${KIMICODE_API_KEY:-}" ]; then
  echo "OK: KIMICODE_API_KEY ist gesetzt."
elif [ -f "$HOME/.kimi/config.toml" ]; then
  echo "OK: ~/.kimi/config.toml vorhanden."
else
  echo "WARNUNG: Kein API-Key. Setze KIMICODE_API_KEY (Key von code.kimi.com → Settings → API Keys)"
  echo "         oder hinterlege ihn in ~/.kimi/config.toml. Ohne Key sind kimi_query/kimi_verify inaktiv."
fi

echo "==> Fertig. In Claude Code mit /mcp prüfen: Server 'kimi-code' mit 8 Tools."
