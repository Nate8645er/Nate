<#
.SYNOPSIS
    Richtet JARVIS als 24/7-Autostart auf Windows ein — OHNE Administratorrechte.

.DESCRIPTION
    - Installiert bei Bedarf Python und die Abhängigkeiten (venv).
    - Legt eine Verknüpfung im Windows-Autostart-Ordner an, die JARVIS bei jeder
      Anmeldung unsichtbar im Hintergrund startet (mit Autopilot).
    - Braucht KEINE geplante Aufgabe und KEINE Adminrechte (deshalb keine
      "Zugriff verweigert"/"Falscher Parameter"-Fehler mehr).

    Dashboard danach jederzeit: http://127.0.0.1:8787

.PARAMETER Port
    Port des Dashboards (Standard 8787).

.PARAMETER Uninstall
    Entfernt die Autostart-Verknüpfung wieder (stoppt den 24/7-Betrieb).
#>
[CmdletBinding()]
param(
    [int]$Port = 8787,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path      # ...\jarvis
$repo = Split-Path -Parent $here                              # Ordner, der 'jarvis' enthält
$startup = [Environment]::GetFolderPath('Startup')
$lnkPath = Join-Path $startup 'JARVIS 24-7.lnk'

function Ok($m)   { Write-Host "  [OK] $m" -ForegroundColor Green }
function Info($m) { Write-Host "  ->  $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "  [!] $m" -ForegroundColor Yellow }

# ---------------------------------------------------------------------------
# Deinstallation
# ---------------------------------------------------------------------------
if ($Uninstall) {
    Write-Host "`nJARVIS 24/7 wird entfernt..." -ForegroundColor Magenta
    if (Test-Path $lnkPath) { Remove-Item $lnkPath -Force; Ok "Autostart-Verknüpfung entfernt." }
    else { Warn "Keine Autostart-Verknüpfung gefunden." }
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*jarvis.run*' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Ok "Fertig. JARVIS startet nicht mehr automatisch."
    return
}

Write-Host @"

  JARVIS 24/7 - Autostart einrichten (ohne Adminrechte)
  =====================================================
"@ -ForegroundColor Magenta

# ---------------------------------------------------------------------------
# 1. Python + venv + Abhängigkeiten
# ---------------------------------------------------------------------------
Info "Prüfe Python..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Warn "Python fehlt - installiere via winget..."
    winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements --silent
    $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path','User')
}
$venv = Join-Path $here '.venv'
$py   = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $py)) {
    Info "Erstelle virtuelle Umgebung..."
    python -m venv $venv
}
Info "Installiere Abhängigkeiten..."
& $py -m pip install -q -r (Join-Path $here 'requirements.txt')
Ok "Python-Umgebung bereit."

# ---------------------------------------------------------------------------
# 2. Headless-Runner (startet JARVIS unsichtbar mit Autopilot)
# ---------------------------------------------------------------------------
$runner = Join-Path $here 'jarvis-service-runner.ps1'
@"
# Auto-generiert - startet JARVIS headless im Hintergrund.
`$env:PYTHONPATH = '$repo'
Set-Location '$repo'
& '$py' -m jarvis.run --autopilot --port $Port
"@ | Set-Content -Path $runner -Encoding UTF8
Ok "Headless-Runner erstellt."

# ---------------------------------------------------------------------------
# 3. Autostart-Verknüpfung im Startup-Ordner (kein Admin, keine geplante Aufgabe)
# ---------------------------------------------------------------------------
Info "Lege Autostart-Verknüpfung an..."
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut($lnkPath)
$s.TargetPath = 'powershell.exe'
$s.Arguments  = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$runner`""
$s.WorkingDirectory = $repo
$s.WindowStyle = 7                         # minimiert/unsichtbar
$s.Description = 'JARVIS HyperScale 24/7'
$s.Save()
Ok "Autostart eingerichtet: JARVIS startet ab jetzt bei jeder Anmeldung."

# ---------------------------------------------------------------------------
# 4. Jetzt sofort starten (unsichtbar)
# ---------------------------------------------------------------------------
Info "Starte JARVIS jetzt..."
Start-Process powershell.exe -WindowStyle Hidden `
    -ArgumentList "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$runner`""
Start-Sleep -Seconds 6
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/state" -UseBasicParsing -TimeoutSec 8
    if ($r.StatusCode -eq 200) { Ok "JARVIS laeuft: http://127.0.0.1:$Port" }
} catch {
    Warn "Dashboard noch nicht erreichbar - gib ihm 10-20s und oeffne dann http://127.0.0.1:$Port"
}

# ---------------------------------------------------------------------------
# 5. Desktop-Verknuepfung zum Dashboard
# ---------------------------------------------------------------------------
try {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $url = Join-Path $desktop 'JARVIS Dashboard.url'
    "[InternetShortcut]`r`nURL=http://127.0.0.1:$Port`r`n" | Set-Content -Path $url -Encoding ASCII
    Ok "Desktop-Verknuepfung 'JARVIS Dashboard' erstellt."
} catch { Warn "Desktop-Verknuepfung konnte nicht erstellt werden (unkritisch)." }

Write-Host @"

  =====================================================================
   JARVIS 24/7 ist eingerichtet (ohne Adminrechte).
  =====================================================================
   Dashboard:  http://127.0.0.1:$Port   (Autopilot laeuft automatisch)
   Autostart:  bei jeder Windows-Anmeldung, unsichtbar im Hintergrund
   Entfernen:  JARVIS-24-7-Entfernen.cmd  (oder -Uninstall)

   Hinweis: Fuer echte KI den API-Key setzen (Fable 5), sonst Offline-Modus.
   24/7 gilt, solange der PC an und du angemeldet bist.
  =====================================================================
"@ -ForegroundColor Green
