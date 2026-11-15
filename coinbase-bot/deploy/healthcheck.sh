#!/usr/bin/env bash
# Simple healthcheck: backend reachable + mode + emergency stop. Exit 0 = ok.
set -euo pipefail
R=$(curl -fsS --max-time 5 http://127.0.0.1:8787/api/health) || { echo "DOWN"; exit 1; }
echo "$R"
