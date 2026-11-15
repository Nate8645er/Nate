#!/usr/bin/env bash
# HyperGrok installer for a persistent Ubuntu/Debian server (e.g. an Oracle
# Cloud Always Free VM). Idempotent: safe to run again. Installs nothing paid,
# binds the backend to 127.0.0.1 only (Cloudflare Tunnel provides HTTPS).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"   # coinbase-bot/
cd "$HERE"

echo "== System-Pakete =="
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip nodejs npm

echo "== Python-Umgebung =="
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt

echo "== Frontend-Build =="
if [ -d web ]; then (cd web && npm ci && npm run build); fi

echo "== Verzeichnisse =="
mkdir -p state logs backups
chmod 700 state

echo "Fertig. Weiter mit deploy/hypergrok.service (systemd) und Cloudflare."
