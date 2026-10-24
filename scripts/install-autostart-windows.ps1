# Installiert JARVIS in den Windows-Autostart: Server + Voice-Satellit
# starten automatisch bei jeder Anmeldung — unsichtbar im Hintergrund.
# Ausführen in PowerShell (im Projektordner):
#   powershell -ExecutionPolicy Bypass -File scripts\install-autostart-windows.ps1

$ErrorActionPreference = "Stop"
$projectDir = Split-Path -Parent $PSScriptRoot

$pythonw = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $pythonw) {
    $python = (Get-Command python -ErrorAction Stop).Source
    $pythonw = Join-Path (Split-Path $python) "pythonw.exe"
}
if (-not (Test-Path $pythonw)) {
    Write-Error "pythonw.exe nicht gefunden - ist Python installiert?"
}

$startup = [Environment]::GetFolderPath("Startup")
$shell = New-Object -ComObject WScript.Shell

# 1) JARVIS Server (unsichtbar)
$lnk = $shell.CreateShortcut((Join-Path $startup "JARVIS Server.lnk"))
$lnk.TargetPath = $pythonw
$lnk.Arguments = "-m jarvis"
$lnk.WorkingDirectory = $projectDir
$lnk.Description = "JARVIS AI OS Server"
$lnk.Save()
Write-Host "OK: JARVIS Server im Autostart"

# 2) Voice-Satellit (unsichtbar, systemweites Mikrofon)
$lnk = $shell.CreateShortcut((Join-Path $startup "JARVIS Voice.lnk"))
$lnk.TargetPath = $pythonw
$lnk.Arguments = "-m jarvis.voice.satellite"
$lnk.WorkingDirectory = $projectDir
$lnk.Description = "JARVIS Voice-Satellit"
$lnk.Save()
Write-Host "OK: JARVIS Voice-Satellit im Autostart (braucht: pip install -e .[voice])"

# 3) Dashboard-Verknuepfung auf dem Desktop
$desktop = [Environment]::GetFolderPath("Desktop")
$lnk = $shell.CreateShortcut((Join-Path $desktop "JARVIS.lnk"))
$lnk.TargetPath = "http://127.0.0.1:8765"
$lnk.Description = "JARVIS Dashboard oeffnen"
$lnk.Save()
Write-Host "OK: Desktop-Verknuepfung 'JARVIS' erstellt"

Write-Host ""
Write-Host "Fertig! Beim naechsten Anmelden laeuft JARVIS automatisch."
Write-Host "Jetzt sofort starten:  Start-Process $pythonw '-m jarvis' ; Start-Process $pythonw '-m jarvis.voice.satellite'"
Write-Host "Entfernen: die JARVIS-Verknuepfungen aus shell:startup loeschen."
