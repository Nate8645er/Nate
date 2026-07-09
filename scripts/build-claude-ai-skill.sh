#!/usr/bin/env bash
# Baut das Upload-Paket fuer Claude.ai (claude.ai -> Settings -> Capabilities -> Skills).
#
# Claude.ai akzeptiert eine ZIP-Datei, die einen Ordner mit SKILL.md enthaelt.
# Dieses Skript verpackt die Skill aus der Plugin-Quelle, damit derselbe
# Orchestrator-Betriebsmodus in Claude Code UND auf Claude.ai laeuft.
#
# Aufruf:
#   scripts/build-claude-ai-skill.sh
# Ergebnis:
#   dist/ultra-enterprise-os-skill.zip

set -euo pipefail
cd "$(dirname "$0")/.."

SRC="ultra-enterprise-os/skills/ultra-enterprise-os"
OUT_DIR="dist"
OUT="$OUT_DIR/ultra-enterprise-os-skill.zip"

[[ -f "$SRC/SKILL.md" ]] || { echo "FEHLER: $SRC/SKILL.md nicht gefunden."; exit 1; }

mkdir -p "$OUT_DIR"
rm -f "$OUT"

if command -v zip >/dev/null 2>&1; then
  (cd "$(dirname "$SRC")" && zip -r "$OLDPWD/$OUT" "$(basename "$SRC")" -x '*.DS_Store')
else
  python3 - "$SRC" "$OUT" <<'PY'
import os, sys, zipfile
src, out = sys.argv[1], sys.argv[2]
base = os.path.dirname(src)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(src):
        for f in files:
            if f == ".DS_Store":
                continue
            p = os.path.join(root, f)
            z.write(p, os.path.relpath(p, base))
PY
fi

echo "Paket gebaut: $OUT"
echo "Upload: claude.ai -> Settings -> Capabilities -> Skills -> Upload skill"
