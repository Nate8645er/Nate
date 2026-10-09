<#
.SYNOPSIS
    Vollautomatische Installation von Claw Code auf Windows.

.DESCRIPTION
    Dieses Skript erledigt die komplette Installation von Claw Code:
      1. Entpackt die heruntergeladene ZIP-Datei (claw-code-main.zip)
      2. Installiert fehlende Abhaengigkeiten (Git, Rust/Cargo, MSVC Build Tools) via winget
      3. Baut Claw Code aus dem Quellcode (cargo build --workspace --release)
      4. Installiert claw.exe nach %LOCALAPPDATA%\Programs\ClawCode
      5. Fuegt das Installationsverzeichnis zum Benutzer-PATH hinzu
      6. Erstellt Desktop- und Startmenue-Verknuepfungen
      7. Fuehrt Funktionspruefungen aus (--version, --help, doctor)
      8. Hinterlegt optional den Anthropic API-Key

.PARAMETER ZipPath
    Pfad zur heruntergeladenen ZIP-Datei. Standard: neueste claw*code*.zip in Downloads.

.PARAMETER AnthropicApiKey
    Optional: Anthropic API-Key (sk-ant-...). Wird als Benutzer-Umgebungsvariable gespeichert.

.PARAMETER SkipShortcuts
    Keine Desktop-/Startmenue-Verknuepfungen anlegen.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Install-ClawCode.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Install-ClawCode.ps1 -ZipPath "$env:USERPROFILE\Downloads\claw-code-main.zip" -AnthropicApiKey "sk-ant-..."

.NOTES
    Benoetigt KEINE Administratorrechte, ausser winget muss Build Tools installieren
    (dann erscheint eine UAC-Abfrage, die bestaetigt werden muss).
#>
[CmdletBinding()]
param(
    [string]$ZipPath,
    [string]$AnthropicApiKey,
    [switch]$SkipShortcuts
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$InstallRoot = Join-Path $env:LOCALAPPDATA 'Programs\ClawCode'
$SourceRoot  = Join-Path $env:LOCALAPPDATA 'ClawCode\src'
$LogFile     = Join-Path $env:TEMP ("clawcode-install-{0:yyyyMMdd-HHmmss}.log" -f (Get-Date))

Start-Transcript -Path $LogFile | Out-Null

function Step($msg)  { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Ok($msg)    { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Warn($msg)  { Write-Host "  [!]  $msg" -ForegroundColor Yellow }
function Fail($msg)  { Write-Host "  [X]  $msg" -ForegroundColor Red; Stop-Transcript | Out-Null; exit 1 }

function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User')
    # Cargo installiert nach %USERPROFILE%\.cargo\bin, das evtl. noch nicht im PATH ist
    $cargoBin = Join-Path $env:USERPROFILE '.cargo\bin'
    if ((Test-Path $cargoBin) -and ($env:Path -notlike "*$cargoBin*")) {
        $env:Path = "$cargoBin;$env:Path"
    }
}

function Test-Cmd($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

function Install-WithWinget($id, $displayName, [string[]]$extraArgs) {
    if (-not (Test-Cmd 'winget')) {
        Fail "winget ist nicht verfuegbar. Bitte 'App Installer' aus dem Microsoft Store installieren und das Skript erneut ausfuehren."
    }
    Step "Installiere $displayName via winget"
    $args = @('install', '--id', $id, '-e', '--accept-source-agreements', '--accept-package-agreements', '--silent') + $extraArgs
    & winget @args
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335189) {  # -1978335189 = bereits installiert
        Warn "winget meldete Exit-Code $LASTEXITCODE fuer $displayName - fahre fort und pruefe erneut."
    }
    Refresh-Path
}

Write-Host @"
   ____ _                  ____          _
  / ___| | __ ___      __ / ___|___   __| | ___
 | |   | |/ _`` \ \ /\ / /| |   / _ \ / _`` |/ _ \
 | |___| | (_| |\ V  V / | |__| (_) | (_| |  __/
  \____|_|\__,_| \_/\_/   \____\___/ \__,_|\___|

  Claw Code - Windows-Installer
"@ -ForegroundColor Magenta

# ---------------------------------------------------------------------------
# Schritt 1: ZIP-Datei finden und entpacken
# ---------------------------------------------------------------------------
Step 'Schritt 1/8: ZIP-Datei suchen und entpacken'

if (-not $ZipPath) {
    $downloads = Join-Path $env:USERPROFILE 'Downloads'
    $candidate = Get-ChildItem -Path $downloads -Filter '*claw*code*.zip' -ErrorAction SilentlyContinue |
                 Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($candidate) { $ZipPath = $candidate.FullName }
}
if (-not $ZipPath -or -not (Test-Path $ZipPath)) {
    Fail "ZIP-Datei nicht gefunden. Bitte mit -ZipPath 'C:\Pfad\zur\claw-code-main.zip' angeben."
}
Ok "ZIP gefunden: $ZipPath"

if (Test-Path $SourceRoot) { Remove-Item $SourceRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $SourceRoot | Out-Null
Expand-Archive -Path $ZipPath -DestinationPath $SourceRoot -Force

# Repo-Wurzel finden (ZIP enthaelt einen Unterordner wie claw-code-main/)
$repoRoot = Get-ChildItem $SourceRoot -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'rust\Cargo.toml') } | Select-Object -First 1
if (-not $repoRoot) {
    if (Test-Path (Join-Path $SourceRoot 'rust\Cargo.toml')) { $repoRoot = Get-Item $SourceRoot }
    else { Fail "Im ZIP wurde kein rust\Cargo.toml gefunden - ist das die richtige Claw-Code-ZIP?" }
}
$rustDir = Join-Path $repoRoot.FullName 'rust'
Ok "Quellcode entpackt nach: $($repoRoot.FullName)"

# ---------------------------------------------------------------------------
# Schritt 2: Abhaengigkeiten pruefen/installieren
# ---------------------------------------------------------------------------
Step 'Schritt 2/8: Abhaengigkeiten pruefen (Git, Rust, MSVC Build Tools)'
Refresh-Path

if (Test-Cmd 'git') { Ok "Git vorhanden: $(git --version)" }
else { Install-WithWinget 'Git.Git' 'Git'; if (Test-Cmd 'git') { Ok 'Git installiert.' } else { Warn 'Git weiterhin nicht im PATH - Build funktioniert trotzdem.' } }

if (-not (Test-Cmd 'cargo')) {
    Install-WithWinget 'Rustlang.Rustup' 'Rust (rustup)'
    Refresh-Path
    if (Test-Cmd 'rustup') { & rustup default stable | Out-Null }
}
if (Test-Cmd 'cargo') { Ok "Rust vorhanden: $(cargo --version)" }
else { Fail "Cargo nicht gefunden. Bitte neues Terminal oeffnen und Skript erneut ausfuehren (PATH-Aktualisierung nach rustup-Installation)." }

# MSVC-Linker pruefen: der Standard-Toolchain 'stable-msvc' braucht die VS Build Tools.
$hasLinker = $false
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vswhere) {
    $vs = & $vswhere -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -latest -property installationPath 2>$null
    if ($vs) { $hasLinker = $true }
}
if (-not $hasLinker) {
    Warn 'MSVC Build Tools (C++-Linker) fehlen. Installation folgt - hierfuer erscheint ggf. eine UAC-/Adminabfrage.'
    Install-WithWinget 'Microsoft.VisualStudio.2022.BuildTools' 'Visual Studio 2022 Build Tools' @(
        '--override', '--quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended'
    )
    Ok 'Build Tools Installation angestossen/abgeschlossen.'
}
else { Ok 'MSVC Build Tools vorhanden.' }

# ---------------------------------------------------------------------------
# Schritt 3: Claw Code bauen
# ---------------------------------------------------------------------------
Step 'Schritt 3/8: Claw Code bauen (cargo build --workspace --release)'
Write-Host '  Das dauert beim ersten Mal einige Minuten...' -ForegroundColor DarkGray

Push-Location $rustDir
try {
    & cargo build --workspace --release
    if ($LASTEXITCODE -ne 0) {
        Warn 'Release-Build fehlgeschlagen - versuche Debug-Build als Fallback.'
        & cargo build --workspace
        if ($LASTEXITCODE -ne 0) { Fail "Build fehlgeschlagen. Log: $LogFile" }
        $builtExe = Join-Path $rustDir 'target\debug\claw.exe'
    }
    else {
        $builtExe = Join-Path $rustDir 'target\release\claw.exe'
    }
}
finally { Pop-Location }

if (-not (Test-Path $builtExe)) { Fail "Build meldete Erfolg, aber $builtExe fehlt." }
Ok "Binary gebaut: $builtExe"

# ---------------------------------------------------------------------------
# Schritt 4: Installation nach %LOCALAPPDATA%\Programs\ClawCode
# ---------------------------------------------------------------------------
Step "Schritt 4/8: Installation nach $InstallRoot"
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
Copy-Item $builtExe (Join-Path $InstallRoot 'claw.exe') -Force
Ok "claw.exe installiert."

# ---------------------------------------------------------------------------
# Schritt 5: PATH aktualisieren
# ---------------------------------------------------------------------------
Step 'Schritt 5/8: Benutzer-PATH aktualisieren'
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($userPath -notlike "*$InstallRoot*") {
    [Environment]::SetEnvironmentVariable('Path', "$userPath;$InstallRoot", 'User')
    Ok "PATH erweitert um: $InstallRoot"
}
else { Ok 'PATH enthaelt ClawCode bereits.' }
Refresh-Path

# ---------------------------------------------------------------------------
# Schritt 6: Verknuepfungen (Desktop + Startmenue)
# ---------------------------------------------------------------------------
Step 'Schritt 6/8: Verknuepfungen erstellen'
if ($SkipShortcuts) { Warn 'Uebersprungen (-SkipShortcuts).' }
else {
    $shell = New-Object -ComObject WScript.Shell
    $targets = @(
        (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Claw Code.lnk'),
        (Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs\Claw Code.lnk')
    )
    foreach ($lnkPath in $targets) {
        $lnkDir = Split-Path $lnkPath -Parent
        New-Item -ItemType Directory -Force -Path $lnkDir | Out-Null
        $lnk = $shell.CreateShortcut($lnkPath)
        # Claw Code ist ein Terminal-Programm: Verknuepfung oeffnet PowerShell mit laufendem claw
        $lnk.TargetPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
        $lnk.Arguments = "-NoExit -Command `"& '$InstallRoot\claw.exe'`""
        $lnk.WorkingDirectory = $env:USERPROFILE
        $lnk.IconLocation = "$InstallRoot\claw.exe,0"
        $lnk.Description = 'Claw Code - CLI Agent Harness'
        $lnk.Save()
        Ok "Verknuepfung: $lnkPath"
    }
}

# ---------------------------------------------------------------------------
# Schritt 7: API-Key (optional)
# ---------------------------------------------------------------------------
Step 'Schritt 7/8: API-Key einrichten'
if ($AnthropicApiKey) {
    [Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', $AnthropicApiKey, 'User')
    $env:ANTHROPIC_API_KEY = $AnthropicApiKey
    Ok 'ANTHROPIC_API_KEY als Benutzer-Umgebungsvariable gespeichert.'
}
elseif ([Environment]::GetEnvironmentVariable('ANTHROPIC_API_KEY', 'User')) {
    Ok 'ANTHROPIC_API_KEY ist bereits gesetzt.'
}
else {
    Warn 'Kein API-Key gesetzt. Claw Code braucht einen Anthropic API-Key (sk-ant-...).'
    Warn 'Spaeter setzen mit:  setx ANTHROPIC_API_KEY "sk-ant-..."'
}

# ---------------------------------------------------------------------------
# Schritt 8: Funktionspruefung
# ---------------------------------------------------------------------------
Step 'Schritt 8/8: Funktionspruefung'
$claw = Join-Path $InstallRoot 'claw.exe'

$ver = & $claw --version 2>&1
if ($LASTEXITCODE -eq 0) { Ok "claw --version -> $ver" } else { Fail "claw --version fehlgeschlagen: $ver" }

& $claw --help *> $null
if ($LASTEXITCODE -eq 0) { Ok 'claw --help funktioniert.' } else { Fail 'claw --help fehlgeschlagen.' }

Write-Host "`n  Ausgabe von 'claw doctor':" -ForegroundColor DarkGray
& $claw doctor
if ($LASTEXITCODE -eq 0) { Ok 'claw doctor erfolgreich.' }
else { Warn 'claw doctor meldete Probleme (haeufig: fehlender API-Key). Nach Setzen des Keys erneut pruefen.' }

# ---------------------------------------------------------------------------
# Fertig
# ---------------------------------------------------------------------------
Write-Host @"

=====================================================================
 Claw Code ist installiert und einsatzbereit!
=====================================================================

 Binary:        $claw
 Im PATH:       ja (neues Terminal oeffnen, dann einfach 'claw' tippen)
 Verknuepfung:  Desktop + Startmenue ('Claw Code')
 Log:           $LogFile

 Erste Schritte (neues PowerShell-Fenster):
   claw --help          Hilfe anzeigen
   claw doctor          Gesundheitscheck
   claw                 interaktive Sitzung starten
   claw prompt "hallo"  Einzel-Prompt

 Hinweis: Fuer Live-Antworten wird ein Anthropic API-Key benoetigt:
   setx ANTHROPIC_API_KEY "sk-ant-..."
=====================================================================
"@ -ForegroundColor Green

Stop-Transcript | Out-Null
