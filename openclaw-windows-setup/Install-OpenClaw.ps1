<#
.SYNOPSIS
    Vollautomatische Installation von Git, Node.js LTS, Claude Code und OpenClaw
    auf Windows 10/11.

.DESCRIPTION
    Das Skript prueft jede Komponente, installiert Fehlendes, repariert typische
    Fehler selbststaendig (PATH, npm-Cache, Execution Policy, Fallback-Quellen)
    und fuehrt am Ende Funktionstests durch:
        openclaw --version
        openclaw doctor
        openclaw gateway status
        claude --version

    Offizielle OpenClaw-Installationsmethode (install.ps1) wird zuerst versucht,
    npm dient als Fallback — exakt wie in docs.openclaw.ai/install beschrieben.

.NOTES
    Ausfuehren in einer PowerShell (am besten "Als Administrator ausfuehren"):
        powershell -ExecutionPolicy Bypass -File .\Install-OpenClaw.ps1

    Parameter:
        -SkipOnboarding   Onboarding (openclaw onboard) nicht starten
        -SkipShortcuts    Keine Desktop-/Startmenue-Verknuepfungen anlegen
#>
[CmdletBinding()]
param(
    [switch]$SkipOnboarding,
    [switch]$SkipShortcuts
)

$ErrorActionPreference = 'Continue'
$LogFile = Join-Path $env:TEMP ("openclaw-setup-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
Start-Transcript -Path $LogFile -Append | Out-Null

# ---------------------------------------------------------------- Hilfsfunktionen

function Write-Step  { param($m) Write-Host "`n==> $m" -ForegroundColor Cyan }
function Write-Ok    { param($m) Write-Host "    [OK] $m" -ForegroundColor Green }
function Write-Warn2 { param($m) Write-Host "    [!]  $m" -ForegroundColor Yellow }
function Write-Fail  { param($m) Write-Host "    [X]  $m" -ForegroundColor Red }

function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    (New-Object Security.Principal.WindowsPrincipal $id).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

# PATH aus der Registry neu laden, damit frisch installierte Tools sofort
# in DIESER Sitzung gefunden werden (sonst waere ein Neustart der Shell noetig).
function Update-SessionPath {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Test-Command { param($name) [bool](Get-Command $name -ErrorAction SilentlyContinue) }

# Befehl mit bis zu 4 Wiederholungen und exponentiellem Backoff ausfuehren
function Invoke-WithRetry {
    param([scriptblock]$Action, [string]$What, [int]$MaxTries = 4)
    for ($i = 1; $i -le $MaxTries; $i++) {
        try {
            & $Action
            if ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) { return $true }
            throw "Exit-Code $LASTEXITCODE"
        } catch {
            if ($i -eq $MaxTries) { Write-Fail "$What fehlgeschlagen: $_"; return $false }
            $wait = [math]::Pow(2, $i)
            Write-Warn2 "$What fehlgeschlagen (Versuch $i/$MaxTries) - neuer Versuch in ${wait}s ..."
            Start-Sleep -Seconds $wait
        }
    }
}

# OpenClaw verlangt Node >=22.22.3 <23  ||  >=24.15.0 <25  ||  >=25.9.0
function Test-NodeVersionOk {
    if (-not (Test-Command node)) { return $false }
    try { $v = [version]((node -v).TrimStart('v')) } catch { return $false }
    return ( ($v.Major -eq 22 -and $v -ge [version]'22.22.3') -or
             ($v.Major -eq 24 -and $v -ge [version]'24.15.0') -or
             ($v.Major -ge 25 -and $v -ge [version]'25.9.0') )
}

# npm-Global-Verzeichnis dauerhaft in den User-PATH aufnehmen, falls es fehlt
function Ensure-NpmGlobalBinOnPath {
    if (-not (Test-Command npm)) { return }
    $npmBin = (npm prefix -g 2>$null)
    if (-not $npmBin) { return }
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    if ($userPath -notlike "*$npmBin*") {
        [Environment]::SetEnvironmentVariable('Path', "$userPath;$npmBin", 'User')
        Write-Ok "npm-Global-Verzeichnis zum PATH hinzugefuegt: $npmBin"
    }
    Update-SessionPath
}

function New-Shortcut {
    param([string]$Path, [string]$Target, [string]$Arguments, [string]$Icon)
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($Path)
    $sc.TargetPath = $Target
    $sc.Arguments  = $Arguments
    if ($Icon) { $sc.IconLocation = $Icon }
    $sc.Save()
}

# ---------------------------------------------------------------- Start

Write-Host ""
Write-Host "=============================================================" -ForegroundColor Magenta
Write-Host "  OpenClaw + Claude Code - Windows Setup"                      -ForegroundColor Magenta
Write-Host "  Protokoll: $LogFile"                                         -ForegroundColor Magenta
Write-Host "=============================================================" -ForegroundColor Magenta

if (-not (Test-IsAdmin)) {
    Write-Warn2 "PowerShell laeuft OHNE Administratorrechte."
    Write-Warn2 "Das meiste funktioniert trotzdem; bei Git-/Node-Installation erscheinen"
    Write-Warn2 "ggf. UAC-Dialoge ('Benutzerkontensteuerung') - diese bitte mit JA bestaetigen."
}

$failures = @()

# ---------------------------------------------------------------- 1) winget

Write-Step "Schritt 1: Paketmanager pruefen (winget)"
$haveWinget = Test-Command winget
if ($haveWinget) { Write-Ok "winget ist verfuegbar." }
else { Write-Warn2 "winget fehlt - es werden direkte Downloads als Fallback benutzt." }

# ---------------------------------------------------------------- 2) Git

Write-Step "Schritt 2: Git pruefen / installieren"
if (Test-Command git) {
    Write-Ok ("Git bereits installiert: " + (git --version))
} else {
    Write-Warn2 "Git nicht gefunden - Installation startet."
    $ok = $false
    if ($haveWinget) {
        $ok = Invoke-WithRetry -What "Git-Installation (winget)" -Action {
            winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements --silent
        }
    }
    if (-not $ok) {
        Write-Warn2 "Fallback: Git direkt von github.com/git-for-windows laden ..."
        $gitUrl = 'https://github.com/git-for-windows/git/releases/latest/download/Git-64-bit.exe'
        $gitExe = Join-Path $env:TEMP 'git-setup.exe'
        $ok = Invoke-WithRetry -What "Git-Download" -Action { Invoke-WebRequest -UseBasicParsing $gitUrl -OutFile $gitExe }
        if ($ok) { Start-Process $gitExe -ArgumentList '/VERYSILENT','/NORESTART' -Wait }
    }
    Update-SessionPath
    if (Test-Command git) { Write-Ok ("Git installiert: " + (git --version)) }
    else { Write-Fail "Git konnte nicht installiert werden."; $failures += 'Git' }
}

# ---------------------------------------------------------------- 3) Node.js LTS

Write-Step "Schritt 3: Node.js LTS pruefen / installieren"
if (Test-NodeVersionOk) {
    Write-Ok ("Node.js erfuellt die OpenClaw-Anforderung: " + (node -v))
} else {
    if (Test-Command node) {
        Write-Warn2 ("Node.js " + (node -v) + " ist zu alt fuer OpenClaw (benoetigt: >=22.22.3 / >=24.15 LTS). Aktualisierung startet.")
    } else {
        Write-Warn2 "Node.js nicht gefunden - LTS-Installation startet."
    }
    $ok = $false
    if ($haveWinget) {
        $ok = Invoke-WithRetry -What "Node.js-Installation (winget)" -Action {
            winget install --id OpenJS.NodeJS.LTS -e --accept-source-agreements --accept-package-agreements --silent
        }
    }
    if (-not $ok) {
        Write-Warn2 "Fallback: Node.js LTS-MSI direkt von nodejs.org laden ..."
        $nodeMsi = Join-Path $env:TEMP 'node-lts.msi'
        $ok = Invoke-WithRetry -What "Node.js-Download" -Action {
            $idx = Invoke-RestMethod 'https://nodejs.org/dist/index.json'
            $lts = ($idx | Where-Object { $_.lts } | Select-Object -First 1).version
            Invoke-WebRequest -UseBasicParsing "https://nodejs.org/dist/$lts/node-$lts-x64.msi" -OutFile $nodeMsi
        }
        if ($ok) { Start-Process msiexec.exe -ArgumentList '/i', $nodeMsi, '/qn', '/norestart' -Wait }
    }
    Update-SessionPath
    if (Test-NodeVersionOk) { Write-Ok ("Node.js installiert: " + (node -v) + " / npm " + (npm -v)) }
    else { Write-Fail "Node.js konnte nicht installiert/aktualisiert werden."; $failures += 'Node.js' }
}

# ---------------------------------------------------------------- 4) Claude Code

Write-Step "Schritt 4: Claude Code pruefen / installieren"
if (Test-Command claude) {
    Write-Ok ("Claude Code bereits installiert: " + (claude --version))
} else {
    Write-Warn2 "Claude Code nicht gefunden - Installation ueber offizielles Skript."
    $ok = Invoke-WithRetry -What "Claude-Code-Installation (claude.ai/install.ps1)" -Action {
        Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
    }
    if (-not $ok -and (Test-Command npm)) {
        Write-Warn2 "Fallback: Installation ueber npm ..."
        $ok = Invoke-WithRetry -What "Claude-Code-Installation (npm)" -Action {
            npm install -g @anthropic-ai/claude-code
        }
    }
    Ensure-NpmGlobalBinOnPath
    Update-SessionPath
    if (Test-Command claude) { Write-Ok ("Claude Code installiert: " + (claude --version)) }
    else { Write-Fail "Claude Code konnte nicht installiert werden."; $failures += 'Claude Code' }
}

# ---------------------------------------------------------------- 5) OpenClaw

Write-Step "Schritt 5: OpenClaw installieren (offizielle Methode, npm als Fallback)"
if (Test-Command openclaw) {
    Write-Ok ("OpenClaw bereits installiert: " + (openclaw --version))
} else {
    # Offizieller Weg laut docs.openclaw.ai/install:
    $ok = Invoke-WithRetry -What "OpenClaw-Installation (openclaw.ai/install.ps1)" -MaxTries 2 -Action {
        Invoke-WebRequest -UseBasicParsing https://openclaw.ai/install.ps1 | Invoke-Expression
    }
    Update-SessionPath
    if (-not (Test-Command openclaw) -and (Test-Command npm)) {
        Write-Warn2 "Offizieller Installer fehlgeschlagen - Fallback auf npm (wie offiziell dokumentiert)."
        npm cache clean --force 2>$null | Out-Null
        $ok = Invoke-WithRetry -What "OpenClaw-Installation (npm)" -Action {
            npm install -g openclaw@latest
        }
    }
    Ensure-NpmGlobalBinOnPath
    Update-SessionPath
    if (Test-Command openclaw) { Write-Ok ("OpenClaw installiert: " + (openclaw --version)) }
    else { Write-Fail "OpenClaw konnte nicht installiert werden."; $failures += 'OpenClaw' }
}

# ---------------------------------------------------------------- 6) Onboarding

if ((Test-Command openclaw) -and (-not $SkipOnboarding)) {
    Write-Step "Schritt 6: OpenClaw-Onboarding starten (interaktiv)"
    Write-Host  "    Der Assistent fragt nach KI-Anbieter/API-Key und Messaging-Kanaelen." -ForegroundColor Gray
    Write-Host  "    '--install-daemon' richtet den Gateway als Windows-Dienst/Autostart ein." -ForegroundColor Gray
    openclaw onboard --install-daemon
    if ($LASTEXITCODE -ne 0) {
        Write-Warn2 "Onboarding meldete Exit-Code $LASTEXITCODE - 'openclaw doctor --fix' versucht Reparatur."
        openclaw doctor --fix
    }
} elseif ($SkipOnboarding) {
    Write-Warn2 "Onboarding uebersprungen (-SkipOnboarding). Spaeter manuell: openclaw onboard --install-daemon"
}

# ---------------------------------------------------------------- 7) Funktionstests

Write-Step "Schritt 7: Funktionstests"
$tests = @(
    @{ Name = 'git --version';            Cmd = { git --version } },
    @{ Name = 'node -v';                  Cmd = { node -v } },
    @{ Name = 'npm -v';                   Cmd = { npm -v } },
    @{ Name = 'claude --version';         Cmd = { claude --version } },
    @{ Name = 'openclaw --version';       Cmd = { openclaw --version } },
    @{ Name = 'openclaw doctor';          Cmd = { openclaw doctor } },
    @{ Name = 'openclaw gateway status';  Cmd = { openclaw gateway status } }
)
foreach ($t in $tests) {
    Write-Host "`n    --- $($t.Name) ---" -ForegroundColor Gray
    try {
        & $t.Cmd
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "Exit-Code $LASTEXITCODE" }
        Write-Ok $t.Name
    } catch {
        Write-Fail "$($t.Name): $_"
        $failures += $t.Name
    }
}

# Gateway ggf. automatisch starten, wenn der Status-Test scheiterte
if ($failures -contains 'openclaw gateway status' -and (Test-Command openclaw)) {
    Write-Warn2 "Gateway laeuft nicht - Startversuch mit 'openclaw gateway start' ..."
    openclaw gateway start
    Start-Sleep -Seconds 5
    openclaw gateway status
    if ($LASTEXITCODE -eq 0) {
        $failures = $failures | Where-Object { $_ -ne 'openclaw gateway status' }
        Write-Ok "Gateway laeuft jetzt."
    }
}

# ---------------------------------------------------------------- 8) Verknuepfungen

if (-not $SkipShortcuts) {
    Write-Step "Schritt 8: Desktop- und Startmenue-Verknuepfungen anlegen"
    $ps = (Get-Command powershell.exe).Source
    $desktop   = [Environment]::GetFolderPath('Desktop')
    $startMenu = Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs'
    $links = @(
        @{ Name = 'OpenClaw Dashboard'; Args = '-NoExit -Command "openclaw dashboard"' },
        @{ Name = 'OpenClaw Status';    Args = '-NoExit -Command "openclaw gateway status; openclaw doctor"' },
        @{ Name = 'Claude Code';        Args = '-NoExit -Command "claude"' }
    )
    foreach ($l in $links) {
        foreach ($dir in @($desktop, $startMenu)) {
            try {
                New-Shortcut -Path (Join-Path $dir "$($l.Name).lnk") -Target $ps -Arguments $l.Args
            } catch { Write-Warn2 "Verknuepfung '$($l.Name)' in '$dir' fehlgeschlagen: $_" }
        }
        Write-Ok "Verknuepfung angelegt: $($l.Name)"
    }
}

# ---------------------------------------------------------------- Zusammenfassung

Write-Host "`n=============================================================" -ForegroundColor Magenta
if ($failures.Count -eq 0) {
    Write-Host "  FERTIG: Alles installiert und einsatzbereit." -ForegroundColor Green
} else {
    Write-Host "  ABGESCHLOSSEN MIT PROBLEMEN bei:" -ForegroundColor Yellow
    $failures | Sort-Object -Unique | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }
    Write-Host "  Details im Protokoll: $LogFile" -ForegroundColor Yellow
    Write-Host "  Tipp: Skript in einer NEUEN PowerShell erneut ausfuehren -" -ForegroundColor Yellow
    Write-Host "  bereits Installiertes wird uebersprungen." -ForegroundColor Yellow
}
Write-Host "=============================================================" -ForegroundColor Magenta

Stop-Transcript | Out-Null
