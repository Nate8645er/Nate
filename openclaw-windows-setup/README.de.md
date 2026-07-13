# OpenClaw + Claude Code — Windows-Setup

Ein Skript, das auf deinem Windows-PC **alles automatisch** installiert und einrichtet:

| Schritt | Was passiert |
|---|---|
| 1 | `winget`-Paketmanager prüfen (Fallback: Direkt-Downloads) |
| 2 | **Git** prüfen → falls fehlend installieren |
| 3 | **Node.js LTS** prüfen (OpenClaw braucht ≥ 22.22.3 bzw. ≥ 24.15) → falls fehlend/zu alt installieren |
| 4 | **Claude Code** installieren (offizielles Skript, npm-Fallback) |
| 5 | **OpenClaw** installieren — zuerst offiziell via `openclaw.ai/install.ps1`, Fallback `npm install -g openclaw@latest` |
| 6 | **Onboarding** starten: `openclaw onboard --install-daemon` (interaktiv) |
| 7 | **Funktionstests**: `openclaw --version`, `openclaw doctor`, `openclaw gateway status`, `claude --version` — Gateway wird bei Bedarf automatisch gestartet |
| 8 | **Desktop- & Startmenü-Verknüpfungen** (OpenClaw Dashboard, OpenClaw Status, Claude Code) |

Fehlerbehandlung ist eingebaut: bis zu 4 Wiederholungen mit Wartezeit, automatische PATH-Reparatur, `npm cache clean`, `openclaw doctor --fix` und Fallback-Downloadquellen. Bereits installierte Komponenten werden erkannt und übersprungen — das Skript kann gefahrlos mehrfach laufen.

## So startest du es (auf deinem Windows-PC)

1. **PowerShell als Administrator öffnen**
   Startmenü → „PowerShell" tippen → Rechtsklick → **„Als Administrator ausführen"** → UAC-Dialog mit **Ja** bestätigen.
   (Ohne Admin geht es auch — dann erscheinen während der Installation einzelne UAC-Abfragen, die du jeweils mit **Ja** bestätigst.)

2. **Repository holen und Skript starten:**

   ```powershell
   git clone https://github.com/Nate8645er/Nate.git
   cd Nate\openclaw-windows-setup
   powershell -ExecutionPolicy Bypass -File .\Install-OpenClaw.ps1
   ```

   Falls Git noch gar nicht installiert ist: Datei `Install-OpenClaw.ps1` einfach über GitHub im Browser herunterladen (Repo → Datei → „Download raw file"), dann:

   ```powershell
   powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Downloads\Install-OpenClaw.ps1"
   ```

3. **Beim Onboarding** stellt dir OpenClaw interaktive Fragen (KI-Anbieter/API-Key, Messaging-Kanäle wie WhatsApp/Telegram). Diese kannst nur du beantworten.

## Was du ggf. bestätigen musst (Administratorrechte)

- **UAC-Dialoge** („Möchten Sie zulassen, dass durch diese App Änderungen … vorgenommen werden?") bei der Installation von Git und Node.js → **Ja**
- Beim Onboarding mit `--install-daemon` richtet OpenClaw den Gateway als Autostart-Dienst ein — auch hier ggf. **Ja** klicken.

## Nützliche Befehle danach

```powershell
openclaw --version          # Version anzeigen
openclaw doctor             # Konfiguration prüfen (mit --fix automatisch reparieren)
openclaw gateway status     # Läuft der Gateway?
openclaw gateway restart    # Gateway neu starten
openclaw dashboard          # Web-Oberfläche öffnen
```

## Hinweise

- **Skript-Optionen:** `-SkipOnboarding` (Onboarding später manuell), `-SkipShortcuts` (keine Verknüpfungen).
- **Protokoll:** Jeder Lauf schreibt ein Log nach `%TEMP%\openclaw-setup-*.log`.
- **WSL2:** Die offizielle Doku empfiehlt für den Gateway auf Windows alternativ WSL2 (Linux-kompatibelste Laufzeit). Das Skript hier nutzt die native Windows-Installation; WSL2 ist optional und unter [docs.openclaw.ai/platforms/windows](https://docs.openclaw.ai/platforms/windows) beschrieben.
- Ein Klonen des Quellcodes (`gh repo clone openclaw/openclaw`) ist für die Installation **nicht nötig** — OpenClaw wird als fertiges npm-Paket installiert.
