#!/usr/bin/env bash
# Vite dev server with a proxy to the backend on 8787.
set -euo pipefail
cd "$(dirname "$0")/web"
[ -d node_modules ] || npm install
exec npm run dev
