#!/usr/bin/env bash
# OmniRoute-Autostart fuer frische Claude-Code-Sitzungen.
# Wird vom SessionStart-Hook im Hintergrund gestartet und blockiert
# den Sitzungsbeginn nicht. Log: /root/.omniroute/autostart.log
#
# Der OpenRouter-Key wird NIE im Repo gespeichert. Er kommt aus der
# Umgebungsvariable OPENROUTER_API_KEY (in den Environment-Einstellungen
# der Claude-Code-Umgebung hinterlegen: claude.ai -> Environments ->
# Environment variables). Ohne Key startet der Server trotzdem, nur
# ohne konfigurierten Provider.

set -u
LOG_DIR="/root/.omniroute"
LOG="$LOG_DIR/autostart.log"
mkdir -p "$LOG_DIR"

{
  echo "=== OmniRoute-Autostart $(date -u +%FT%TZ) ==="

  if ! command -v npm >/dev/null 2>&1; then
    echo "npm nicht gefunden, Abbruch."
    exit 0
  fi

  if ! command -v omniroute >/dev/null 2>&1; then
    echo "Installiere omniroute (einmalig pro Sitzung, ~2 Min) ..."
    npm install -g omniroute >>"$LOG" 2>&1 || { echo "Installation fehlgeschlagen."; exit 0; }
  else
    echo "omniroute bereits installiert: $(omniroute --version 2>/dev/null | tail -1)"
  fi

  if omniroute providers list 2>/dev/null | grep -qi "openrouter.*active"; then
    echo "OpenRouter-Provider bereits konfiguriert, ueberspringe Key-Schritt."
  elif [ -n "${OPENROUTER_API_KEY:-}" ]; then
    # Key-Hinterlegung funktioniert nur direkt auf der DB (Server gestoppt).
    omniroute stop >/dev/null 2>&1 || true
    sleep 2
    omniroute keys add openrouter "$OPENROUTER_API_KEY" >>"$LOG" 2>&1 \
      && echo "OpenRouter-Key aus Umgebungsvariable hinterlegt." \
      || echo "Key-Hinterlegung fehlgeschlagen (siehe Log)."
  else
    echo "OPENROUTER_API_KEY nicht gesetzt — Server startet ohne Provider."
  fi

  if curl -s -o /dev/null -m 3 "http://localhost:20128/v1/models"; then
    echo "Server laeuft bereits."
  else
    echo "Starte OmniRoute-Server ..."
    nohup omniroute serve >>"$LOG_DIR/serve.log" 2>&1 &
    disown || true
    for i in $(seq 1 12); do
      sleep 5
      if curl -s -o /dev/null -m 3 "http://localhost:20128/v1/models"; then
        echo "Server erreichbar nach ~$((i*5))s."
        break
      fi
    done
  fi

  echo "=== Autostart fertig ==="
} >>"$LOG" 2>&1
