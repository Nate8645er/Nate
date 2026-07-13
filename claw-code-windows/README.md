# Claw Code – Windows-Installation

Vollautomatischer Installer für [Claw Code](https://github.com/ultraworkers/claw-code)
(Rust-CLI-Agent-Harness, Build aus dem Quellcode) auf Windows 10/11.

## Was der Installer macht

| Schritt | Aktion |
|---|---|
| 1 | Entpackt die heruntergeladene `claw-code-main.zip` (findet sie automatisch in `Downloads`) |
| 2 | Installiert fehlende Abhängigkeiten per `winget`: **Git**, **Rust (rustup)**, **Visual Studio 2022 Build Tools** (C++-Linker) |
| 3 | Baut Claw Code: `cargo build --workspace --release` (Fallback: Debug-Build) |
| 4 | Installiert `claw.exe` nach `%LOCALAPPDATA%\Programs\ClawCode` |
| 5 | Fügt das Verzeichnis dem **Benutzer-PATH** hinzu |
| 6 | Erstellt **Desktop- und Startmenü-Verknüpfung** („Claw Code“, öffnet PowerShell mit laufendem `claw`) |
| 7 | Hinterlegt optional den `ANTHROPIC_API_KEY` |
| 8 | Prüft die Installation: `claw --version`, `claw --help`, `claw doctor` |

Der Quellcode wurde bereits verifiziert: Der Workspace kompiliert fehlerfrei und
`claw --version` / `--help` / `doctor` laufen erfolgreich durch (0 Failures).

## Ausführen

1. `Install-ClawCode.ps1` auf den PC kopieren (z. B. in `Downloads`, neben die ZIP).
2. PowerShell öffnen (normale Rechte genügen) und ausführen:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-ClawCode.ps1
```

Mit explizitem ZIP-Pfad und API-Key:

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-ClawCode.ps1 `
    -ZipPath "$env:USERPROFILE\Downloads\claw-code-main.zip" `
    -AnthropicApiKey "sk-ant-..."
```

### Wann Bestätigungen nötig sind

- **UAC-/Admin-Abfrage**: nur falls die Visual Studio Build Tools noch fehlen –
  deren Installation durch winget löst eine Windows-Bestätigung aus. Einfach bestätigen,
  das Skript arbeitet danach weiter.
- Falls Rust gerade frisch installiert wurde und `cargo` im selben Fenster noch nicht
  gefunden wird: neues Terminal öffnen und das Skript erneut starten (es ist idempotent –
  bereits erledigte Schritte werden übersprungen).

## Nach der Installation

Neues Terminal öffnen, dann:

```powershell
claw --help          # Hilfe
claw doctor          # Gesundheitscheck
claw                 # interaktive Sitzung (REPL)
claw prompt "hallo"  # Einzel-Prompt
```

**Wichtig:** Claw Code benötigt für Live-Antworten einen **Anthropic API-Key**
(`sk-ant-...`, von https://console.anthropic.com – ein Claude-Abo reicht nicht):

```powershell
setx ANTHROPIC_API_KEY "sk-ant-..."
```

Danach neues Terminal öffnen und `claw doctor` erneut ausführen – dann sind alle
Funktionen aktiv. Alternativ werden auch OpenAI-kompatible Provider unterstützt
(`OPENAI_API_KEY` / `OPENAI_BASE_URL`, z. B. OpenRouter oder lokales Ollama) –
Details in `docs/windows-install-release.md` im entpackten Quellcode.

## Hinweise

- Claw Code ist ein Community-Projekt (MIT-Lizenz) und **nicht mit Anthropic affiliiert**.
- Das Installationslog liegt unter `%TEMP%\clawcode-install-*.log`.
- Deinstallation: Ordner `%LOCALAPPDATA%\Programs\ClawCode` löschen, PATH-Eintrag
  entfernen, Verknüpfungen löschen.
