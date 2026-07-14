# JARVIS HyperScale - Windows-Starter
# Installiert die Python-Abhaengigkeiten (einmalig) und startet das Dashboard.
# Aufruf:  powershell -ExecutionPolicy Bypass -File .\Start-Jarvis.ps1 [-Demo] [-Autopilot] [-Setup]
#   -Setup : einmalige PC-Einrichtung (PC-Zusaetze, Browser-Treiber, Desktop-Symbol)
param([switch]$Demo, [switch]$Autopilot, [switch]$Setup)

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

Write-Host ""
Write-Host "JARVIS startet - Dashboard: http://127.0.0.1:8787" -ForegroundColor Green
Start-Process "http://127.0.0.1:8787"
& $py @argv
