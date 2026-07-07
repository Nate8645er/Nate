#!/usr/bin/env bash
# Installiert JARVIS als systemd-User-Dienste: Server + Voice-Satellit
# starten automatisch bei jeder Anmeldung. Ausführen mit:
#   bash scripts/install-autostart-linux.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JARVIS_BIN="$(command -v jarvis || true)"
JARVIS_VOICE_BIN="$(command -v jarvis-voice || true)"

if [[ -z "$JARVIS_BIN" ]]; then
  echo "FEHLER: 'jarvis' nicht gefunden. Erst installieren: pip install -e ." >&2
  exit 1
fi

UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"

cat > "$UNIT_DIR/jarvis.service" <<EOF
[Unit]
Description=JARVIS AI OS Server
After=network-online.target

[Service]
WorkingDirectory=$PROJECT_DIR
ExecStart=$JARVIS_BIN
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now jarvis.service
echo "✓ jarvis.service läuft und startet künftig automatisch"

if [[ -n "$JARVIS_VOICE_BIN" ]]; then
  cat > "$UNIT_DIR/jarvis-voice.service" <<EOF
[Unit]
Description=JARVIS Voice-Satellit (Mikrofon, systemweit)
After=jarvis.service sound.target

[Service]
WorkingDirectory=$PROJECT_DIR
ExecStart=$JARVIS_VOICE_BIN
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
  systemctl --user daemon-reload
  systemctl --user enable --now jarvis-voice.service
  echo "✓ jarvis-voice.service läuft — sag einfach 'Jarvis…'"
else
  echo "Hinweis: Voice-Satellit nicht installiert."
  echo "         Aktivieren mit: pip install -e '.[voice]' && bash $0"
fi

echo
echo "Status:   systemctl --user status jarvis jarvis-voice"
echo "Logs:     journalctl --user -u jarvis -f"
echo "Stoppen:  systemctl --user disable --now jarvis jarvis-voice"
