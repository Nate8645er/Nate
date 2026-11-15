#!/usr/bin/env bash
# Railway start command. Railway sets $PORT and publishes the app over HTTPS,
# so the backend must bind 0.0.0.0:$PORT (unlike the private 127.0.0.1 default).
# The trading API is then reachable at the Railway URL and is protected ONLY by
# the dashboard login + CSRF + the hard trading locks. LIVE AUTONOMOUS stays
# locked; put Cloudflare Access in front if you want the e-mail gate too.
#
# Secrets (passphrase, portfolio id) come from Railway environment variables,
# never from git. Attach a Railway VOLUME at coinbase-bot/state so the encrypted
# key, loss ledger and emergency stop survive redeploys.
set -euo pipefail
PORT="${PORT:-8787}"
PY=".venv/bin/python"; [ -x "$PY" ] || PY="python"
exec "$PY" -m uvicorn server.app:app --host 0.0.0.0 --port "$PORT" --log-level warning
