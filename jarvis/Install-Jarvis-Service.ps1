<#
.SYNOPSIS
    Richtet JARVIS als 24/7-Hintergrunddienst auf Windows ein (geplante Aufgabe).

.DESCRIPTION
    - Installiert bei Bedarf Python und die Abhängigkeiten (venv).
    - Registriert eine geplante Aufgabe "JARVIS 24/7", die bei jeder Anmeldung
      automatisch und unsichtbar startet, den Autopilot aktiviert und sich bei
      einem Absturz selbst neu startet.
    - Läuft komplett ohne Administratorrechte (Aufgabe im Benutzerkontext).

    Danach läuft JARVIS im Hintergrund, sobald du dich an Windows anmeldest —
    auch wenn kein Fenster offen ist. Das Dashboard erreichst du jederzeit unter
    http://127.0.0.1:8787

.PARAMETER Port
    Port des Dashboards (Standard 8787).

.PARAMETER Uninstall
    Entfernt die geplante Aufgabe wieder (stoppt den 24/7-Betrieb).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Install-Jarvis-Service.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\Install-Jarvis-Service.ps1 -Uninstall

.NOTES
    24/7 gilt, solange dein PC eingeschaltet (und du angemeldet) bist. Für echten
    Dauerbetrieb auch ohne Anmeldung wäre ein immer laufender Rechner/Server nötig.
#>
[CmdletBinding()]
param(
    [int]$Port = 8787,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$TaskName = 'JARVIS 24/7'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path      # ...\jarvis
$repo = Split-Path -Parent $here                              # Ordner, der 'jarvis' enthält

function Ok($m)   { Write-Host "  [OK] $m" -ForegroundColor Green }
function Info($m) { Write-Host "  ->  $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "  [!] $m" -ForegroundColor Yellow }

# ---------------------------------------------------------------------------
# Deinstallation
# ---------------------------------------------------------------------------
if ($Uninstall) {
    Write-Host "`nJARVIS 24/7 wird entfernt..." -ForegroundColor Magenta
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Ok "Geplante Aufgabe '$TaskName' entfernt. JARVIS startet nicht mehr automatisch."
    } else {
        Warn "Keine geplante Aufgabe '$TaskName' gefunden."
    }
    # laufende Instanz beenden
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*jarvis.run*' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Ok "Fertig."
    return
}

Write-Host @"

  JARVIS 24/7 - Hintergrunddienst einrichten
  ==========================================
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
# 2. Start-Skript für den Dienst (headless, mit Autopilot, ohne Browser-Popup)
# ---------------------------------------------------------------------------
$runner = Join-Path $here 'jarvis-service-runner.ps1'
@"
# Auto-generiert von Install-Jarvis-Service.ps1 - startet JARVIS headless im Hintergrund.
`$env:PYTHONPATH = '$repo'
Set-Location '$repo'
& '$py' -m jarvis.run --autopilot --port $Port
"@ | Set-Content -Path $runner -Encoding UTF8
Ok "Dienst-Runner erstellt: $runner"

# ---------------------------------------------------------------------------
# 3. Geplante Aufgabe registrieren (Anmeldung + Neustart bei Absturz)
# ---------------------------------------------------------------------------
Info "Registriere geplante Aufgabe '$TaskName'..."
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$runner`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description 'JARVIS HyperScale 24/7 Autopilot' | Out-Null
Ok "Aufgabe registriert (startet bei jeder Anmeldung, Neustart bei Absturz)."

# ---------------------------------------------------------------------------
# 4. Sofort starten
# ---------------------------------------------------------------------------
Info "Starte JARVIS jetzt..."
Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 6
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/state" -UseBasicParsing -TimeoutSec 8
    if ($r.StatusCode -eq 200) { Ok "JARVIS laeuft: http://127.0.0.1:$Port" }
} catch {
    Warn "Dashboard noch nicht erreichbar - gib ihm 10-20s beim ersten Start und oeffne dann http://127.0.0.1:$Port"
}

# ---------------------------------------------------------------------------
# 5. Desktop-Verknuepfung zum Dashboard (zum Oeffnen ohne PowerShell)
# ---------------------------------------------------------------------------
try {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $url = Join-Path $desktop 'JARVIS Dashboard.url'
    "[InternetShortcut]`r`nURL=http://127.0.0.1:$Port`r`n" | Set-Content -Path $url -Encoding ASCII
    Ok "Desktop-Verknuepfung 'JARVIS Dashboard' erstellt."
} catch { Warn "Desktop-Verknuepfung konnte nicht erstellt werden (unkritisch)." }

Write-Host @"

  =====================================================================
   JARVIS 24/7 ist eingerichtet.
  =====================================================================
   Dashboard:     http://127.0.0.1:$Port   (Autopilot laeuft automatisch)
   Autostart:     bei jeder Windows-Anmeldung, unsichtbar im Hintergrund
   Neustart:      automatisch bei Absturz (jede Minute erneut)
   Stoppen/Entfernen:
       powershell -ExecutionPolicy Bypass -File .\Install-Jarvis-Service.ps1 -Uninstall

   Hinweis: Fuer echte KI-Ideen den API-Key setzen (FABLE 5), sonst laeuft
   der Autopilot im kostenlosen Offline-Modus. 24/7 gilt, solange der PC an ist.
  =====================================================================
"@ -ForegroundColor Green
