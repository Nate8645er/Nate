#!/usr/bin/env bash
# Google Compute Engine startup script for a FREE e2-micro VM (1 GB RAM).
# Paste this into: VM anlegen -> Erweitert -> Verwaltung -> Automatisierung ->
# "Startskript". It runs as root on every boot and is idempotent.
#
# It does NOT reach Coinbase and runs no trade. The backend binds to 127.0.0.1
# only; HTTPS comes from Cloudflare Tunnel (set up separately, your login).
set -euxo pipefail

# --- settings you may change -------------------------------------------------
REPO_URL="https://github.com/Nate8645er/Nate.git"
BRANCH="claude/coinbase-ai-trading-bot-f6i4h3"
APP_USER="hypergrok"
APP_HOME="/opt/hypergrok"
SUBDIR="coinbase-bot"
# For a PRIVATE repo, put a read-only token in the VM metadata key GITHUB_TOKEN
# (Console -> VM -> Edit -> Metadata). Never bake a token into this script.
TOKEN="$(curl -s -H 'Metadata-Flavor: Google' \
  'http://metadata.google.internal/computeMetadata/v1/instance/attributes/GITHUB_TOKEN' || true)"
if [ -n "${TOKEN:-}" ]; then
  REPO_URL="https://x-access-token:${TOKEN}@github.com/Nate8645er/Nate.git"
fi
# ----------------------------------------------------------------------------

# 1 GB RAM is tight: add 2 GB swap so pip/npm are not OOM-killed.
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile; mkswap /swapfile; swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-pip git curl nodejs npm

id "$APP_USER" >/dev/null 2>&1 || useradd -m -d "$APP_HOME" -s /bin/bash "$APP_USER"
mkdir -p "$APP_HOME"; chown -R "$APP_USER":"$APP_USER" "$APP_HOME"

# Clone or update the repo as the app user.
sudo -u "$APP_USER" bash <<USR
set -eux
cd "$APP_HOME"
if [ -d Nate/.git ]; then
  cd Nate && git fetch --depth 1 origin "$BRANCH" && git checkout "$BRANCH" && git reset --hard origin/"$BRANCH"
else
  git clone --depth 1 -b "$BRANCH" "$REPO_URL" Nate
  cd Nate
fi
cd "$SUBDIR"
python3 -m venv .venv
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet -r requirements.txt
# Frontend build needs memory; cap Node heap and lean on swap.
if [ -d web ]; then (cd web && NODE_OPTIONS=--max-old-space-size=512 npm ci && NODE_OPTIONS=--max-old-space-size=512 npm run build); fi
mkdir -p state logs backups; chmod 700 state
USR

APP_DIR="$APP_HOME/Nate/$SUBDIR"

# systemd service: auto-start on boot, auto-restart, memory-guarded for 1 GB.
cat > /etc/systemd/system/hypergrok.service <<UNIT
[Unit]
Description=HyperGrok AI Trading Backend (127.0.0.1 only)
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python -m uvicorn server.app:app --host 127.0.0.1 --port 8787 --log-level warning
Restart=always
RestartSec=5
MemoryMax=450M
NoNewPrivileges=true
PrivateTmp=true
[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now hypergrok.service
echo "HyperGrok startup-script fertig."
