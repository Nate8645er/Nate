#!/bin/bash
# Startet den offiziellen Playwright MCP (@playwright/mcp) mit den
# Workarounds fuer Claude-Code-Remote-Container:
#  - vorinstalliertes Chromium (/opt/pw-browsers) statt Browser-Download
#  - headless + ohne Sandbox (Container laeuft als root, kein DISPLAY)
#  - Egress-Proxy: --proxy-server aus HTTPS_PROXY plus
#    --ssl-version-max=tls1.2 (der Gateway resettet TLS-1.3-ClientHellos)
# Auf Systemen ohne diese Besonderheiten verhaelt sich das Skript neutral.
set -u
CFG="${TMPDIR:-/tmp}/playwright-mcp-config.json"

ARGS_JSON='[]'
if [ -n "${HTTPS_PROXY:-}" ]; then
  ARGS_JSON="[\"--proxy-server=${HTTPS_PROXY}\", \"--ssl-version-max=tls1.2\"]"
fi

EXEC_PATH=""
[ -x /opt/pw-browsers/chromium ] && EXEC_PATH='"executablePath": "/opt/pw-browsers/chromium",'

HEADLESS="false"
[ -z "${DISPLAY:-}" ] && HEADLESS="true"

cat > "$CFG" << EOF
{
  "browser": {
    "browserName": "chromium",
    "launchOptions": {
      $EXEC_PATH
      "headless": $HEADLESS,
      "chromiumSandbox": false,
      "args": $ARGS_JSON
    }
  }
}
EOF

exec npx -y @playwright/mcp@latest --config "$CFG" "$@"
