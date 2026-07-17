# JARVIS HyperScale - Windows-Starter
# Installiert die Python-Abhaengigkeiten (einmalig) und startet das Dashboard.
# Aufruf:  powershell -ExecutionPolicy Bypass -File .\Start-Jarvis.ps1 [-Demo] [-Autopilot] [-Setup]
#   -Setup : einmalige PC-Einrichtung (PC-Zusaetze, Browser-Treiber, Desktop-Symbol)
param([switch]$Demo, [switch]$Autopilot, [switch]$Setup, [switch]$Lan)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Split-Path -Parent $here   # Ordner, der 'jarvis' enthaelt

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python fehlt - installiere via winget..." -ForegroundColor Yellow
    winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements --silent
    $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path','User')
}

$venv = Join-Path $here '.venv'
if (-not (Test-Path $venv)) {
    Write-Host "Erstelle virtuelle Umgebung..." -ForegroundColor Cyan
    python -m venv $venv
}
$py = Join-Path $venv 'Scripts\python.exe'
& $py -m pip install -q -r (Join-Path $here 'requirements.txt')

# --- Einmalige PC-Einrichtung -------------------------------------------------
if ($Setup) {
    Write-Host "Richte PC-Funktionen ein (Maus/Tastatur, Browser-Steuerung)..." -ForegroundColor Cyan
    # PC-Zusaetze sind in requirements.txt fuer Windows bereits enthalten (pyautogui, pillow, playwright).
    # Browser-Treiber (Chromium) fuer die Browser-Automatisierung - best effort, blockiert nie den Start:
    try { & $py -m playwright install chromium 2>$null } catch { Write-Host "  (Browser-Treiber uebersprungen - Edge/Chrome wird sonst genutzt)" -ForegroundColor DarkGray }

    # Desktop-Symbol anlegen, das JARVIS-Starten.cmd startet
    try {
        $desktop = [Environment]::GetFolderPath('Desktop')
        $lnk = Join-Path $desktop 'JARVIS starten.lnk'
        $target = Join-Path $here 'JARVIS-Starten.cmd'
        $ws = New-Object -ComObject WScript.Shell
        $s = $ws.CreateShortcut($lnk)
        $s.TargetPath = $target
        $s.WorkingDirectory = $here
        $s.Description = 'JARVIS HyperScale starten'
        $s.Save()
        Write-Host "  Desktop-Symbol erstellt: 'JARVIS starten'" -ForegroundColor Green
    } catch { Write-Host "  (Desktop-Symbol konnte nicht erstellt werden)" -ForegroundColor DarkGray }
}

$env:PYTHONPATH = $repo
$argv = @('-m', 'jarvis.run')
if ($Demo) { $argv += '--demo' }
if ($Autopilot) { $argv += '--autopilot' }
if ($Lan) { $argv += '--lan' }

$url = 'http://127.0.0.1:8787'
# Im Handy-Modus die HANDY-Seite mit QR-Code oeffnen (zum Scannen mit dem Handy).
$openUrl = if ($Lan) { "$url/handy" } else { $url }
Write-Host ""
Write-Host "JARVIS startet als eigene App..." -ForegroundColor Green

# Server im Hintergrund starten (verbindet sich automatisch mit PC + Keys)
$server = Start-Process -FilePath $py -ArgumentList $argv -WorkingDirectory $repo -PassThru -WindowStyle Hidden

# Warten bis das Dashboard antwortet
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 700
    try { if ((Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { break } } catch {}
}

# JARVIS als EIGENE APP oeffnen (Edge/Chrome App-Modus = eigenes Fenster, keine Browser-Leiste)
$edge = @("$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
          "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe") |
        Where-Object { Test-Path $_ } | Select-Object -First 1
$chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
            "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe") |
          Where-Object { Test-Path $_ } | Select-Object -First 1
if ($edge)      { Start-Process $edge   "--app=$openUrl --window-size=1500,950" }
elseif ($chrome){ Start-Process $chrome "--app=$openUrl --window-size=1500,950" }
else            { Start-Process $openUrl }

Write-Host "JARVIS-App geoeffnet. Dieses kleine Fenster offen lassen (hier laeuft JARVIS)." -ForegroundColor Green
Write-Host "Zum Beenden dieses Fenster schliessen." -ForegroundColor DarkGray
# Server im Vordergrund halten, bis er endet
Wait-Process -Id $server.Id
