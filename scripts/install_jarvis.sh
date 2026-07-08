#!/usr/bin/env bash
# Installiert Open Jarvis (https://open-jarvis.github.io) in die aktuelle Umgebung.
#
# In Claude-Code-Cloud-Sessions laeuft dieses Skript automatisch beim Session-Start
# (SessionStart-Hook in .claude/settings.json). Voraussetzung: die Domain
# open-jarvis.github.io ist in der Netzwerk-Policy der Umgebung erlaubt
# (claude.ai/code -> Umgebung bearbeiten -> Network access: Custom ->
#  "open-jarvis.github.io" eintragen). Ist sie blockiert, wird die Installation
# still uebersprungen und die Session startet normal.
#
# Manuell auf dem eigenen Rechner ausfuehren mit:
#   scripts/install_jarvis.sh --local

set -u

MARKER="${HOME}/.open-jarvis-installed"
URL="https://open-jarvis.github.io/install.sh"

# Ohne --local nur in Cloud-Sessions automatisch installieren,
# damit der Hook nicht ungefragt auf lokalen Rechnern installiert.
if [ "${1:-}" != "--local" ] && [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

if [ -f "$MARKER" ]; then
  echo "open-jarvis: bereits installiert (Marker: $MARKER)." >&2
  exit 0
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

if ! curl -fsSL "$URL" -o "$TMP"; then
  echo "open-jarvis: $URL nicht erreichbar (Netzwerk-Policy der Umgebung?). Installation uebersprungen." >&2
  exit 0
fi

echo "open-jarvis: Installer geladen ($(wc -c < "$TMP") Bytes), starte Installation..." >&2
if bash "$TMP"; then
  touch "$MARKER"
  echo "open-jarvis: Installation abgeschlossen." >&2
else
  echo "open-jarvis: Installer meldete einen Fehler (Session laeuft trotzdem weiter)." >&2
fi

exit 0
