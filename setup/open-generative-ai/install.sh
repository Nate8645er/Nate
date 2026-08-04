#!/usr/bin/env bash
# Open Generative AI - reproduzierbare Installation.
#
# Diese Sitzungsumgebung ist fluechtig: alles ausserhalb des Repos wird
# geloescht. Dieses Skript ist deshalb die dauerhafte Form der Installation -
# es stellt sie in jeder neuen Sitzung in wenigen Minuten wieder her.
#
# Am 4.8.2026 vollstaendig durchgelaufen und verifiziert:
#   npm install 1044 Pakete, 3 Untermodule geklont, build:packages OK,
#   next build OK, Server auf Port 3007 mit HTTP 200 auf /studio,
#   Modellkatalog liefert 504 Eintraege.
#
# Aufruf:  bash setup/open-generative-ai/install.sh [zielverzeichnis]
set -euo pipefail

ZIEL="${1:-$HOME/open-generative-ai}"
PORT="${OGA_PORT:-3007}"

echo "==> Ziel: $ZIEL"

if [ ! -d "$ZIEL/.git" ] && [ ! -f "$ZIEL/package.json" ]; then
  echo "==> Hauptprojekt klonen"
  git clone --depth 1 https://github.com/SamurAIGPT/Open-Generative-AI.git "$ZIEL"
fi
cd "$ZIEL"

# Die drei Untermodule sind in ZIP-Downloads IMMER leer. Ohne sie schlaegt
# der Next.js-Build mit "Module not found: ai-agent" fehl.
echo "==> Untermodule holen"
mkdir -p packages
klone() {  # $1 = repo, $2 = zielordner
  local ziel="packages/$2"
  if [ ! -f "$ziel/package.json" ]; then
    rm -rf "$ziel"
    git clone --depth 1 "https://github.com/$1.git" "$ziel"
  fi
  local n; n=$(find "$ziel" -type f | wc -l)
  echo "    $2: $n Dateien"
  [ "$n" -gt 0 ] || { echo "    FEHLER: $2 leer geblieben"; return 1; }
}
klone "Anil-matcha/Open-Poe-AI"          "Open-Poe-AI"
klone "SamurAIGPT/Vibe-Workflow"         "Vibe-Workflow"
klone "Anil-matcha/Open-AI-Design-Agent" "Open-AI-Design-Agent"

echo "==> Abhaengigkeiten (belegt rund 1.4 GB)"
npm install --no-audit --no-fund

echo "==> Arbeitsbereiche bauen"
npm run build:packages

echo "==> Anwendung bauen"
npm run build

echo
echo "==> Fertig. Starten mit:"
echo "    cd $ZIEL && npx next start -p $PORT"
echo
echo "WICHTIG: Ohne MuAPI-Schluessel liefert jede Generierung"
echo "  {\"detail\":\"Not authorized: missing or invalid credentials\"}"
echo "Schluessel gibt es unter https://muapi.ai/access-keys, danach:"
echo "    export MUAPI_KEY=...   (oder im Fenster \"API Key\" der Oberflaeche)"
