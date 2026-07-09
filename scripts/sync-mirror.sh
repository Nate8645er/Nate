#!/usr/bin/env bash
# Harmonisiert Plugin-Quelle und Claude-Code-Spiegel.
#
# Quelle der Wahrheit:  ultra-enterprise-os/   (Plugin, via Marketplace installierbar)
# Spiegel:              .claude/               (laedt automatisch in jeder Session)
#
# Aufrufe:
#   scripts/sync-mirror.sh          # synchronisiert Quelle -> Spiegel
#   scripts/sync-mirror.sh --check  # prueft nur auf Drift (Exit 1 bei Abweichung)

set -euo pipefail
cd "$(dirname "$0")/.."

SRC="ultra-enterprise-os"
PAIRS=(
  "$SRC/skills:.claude/skills"
  "$SRC/agents:.claude/agents"
  "$SRC/commands:.claude/commands"
)

if [[ "${1:-}" == "--check" ]]; then
  status=0
  for pair in "${PAIRS[@]}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    if ! diff -r "$src" "$dst" >/dev/null 2>&1; then
      echo "DRIFT: $src <-> $dst"
      diff -rq "$src" "$dst" || true
      status=1
    fi
  done
  [[ $status -eq 0 ]] && echo "OK: Plugin-Quelle und .claude/-Spiegel sind identisch."
  exit $status
fi

for pair in "${PAIRS[@]}"; do
  src="${pair%%:*}"; dst="${pair##*:}"
  rm -rf "$dst"
  mkdir -p "$(dirname "$dst")"
  cp -R "$src" "$dst"
  echo "synchronisiert: $src -> $dst"
done
echo "Fertig. Spiegel ist auf dem Stand der Plugin-Quelle."
