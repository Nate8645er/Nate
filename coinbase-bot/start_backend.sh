#!/usr/bin/env bash
# Starts the HyperGrok backend on 127.0.0.1 only. Never bind this to 0.0.0.0
# without a reverse proxy and TLS: it drives a real trading connector.
set -euo pipefail
cd "$(dirname "$0")"
export HYPERGROK_TOKEN="${HYPERGROK_TOKEN:-$(python -c 'import secrets;print(secrets.token_urlsafe(24))')}"
echo "============================================================"
echo "Dashboard-Token (nur hier, nie im Repo):"
echo "  $HYPERGROK_TOKEN"
echo "============================================================"
exec python -m uvicorn server.app:app --host 127.0.0.1 --port 8787 --log-level warning
