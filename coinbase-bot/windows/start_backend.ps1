# HyperGrok backend for Windows 11. Run from PowerShell:
#   powershell -ExecutionPolicy Bypass -File windows\start_backend.ps1
# Installs nothing system-wide: a Python venv inside the project folder only.
# Binds to 127.0.0.1. After every (re)start the system is in PAPER mode and an
# emergency stop that was active before is still active.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".venv")) {
    Write-Host "Erstelle Python-Umgebung (.venv) ..."
    python -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install --quiet --disable-pip-version-check -r requirements.txt

# Load .env into THIS process only (not into Windows, not into the registry).
if (Test-Path ".env") {
    Get-Content ".env" | Where-Object { $_ -match "^\s*[^#\s][^=]*=" } | ForEach-Object {
        $name, $value = $_ -split "=", 2
        if ($value.Trim()) { [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process") }
    }
}

# Log management: one file, rotated at 5 MB, five generations kept.
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
$Log = "logs\backend.log"
if ((Test-Path $Log) -and ((Get-Item $Log).Length -gt 5MB)) {
    for ($i = 4; $i -ge 1; $i--) {
        if (Test-Path "$Log.$i") { Move-Item -Force "$Log.$i" "$Log.$($i + 1)" }
    }
    Move-Item -Force $Log "$Log.1"
}

if (-not (Test-Path "web\dist\index.html")) {
    Write-Host "Hinweis: web\dist fehlt. Einmal windows\build_frontend.ps1 ausfuehren." -ForegroundColor Yellow
}

# Restart recovery: if the backend exits unexpectedly, start it again after a
# pause. Stop with Ctrl+C. Five crashes within the loop end it for good.
$crashes = 0
while ($crashes -lt 5) {
    Write-Host "Starte Backend auf http://127.0.0.1:8787  (Strg+C beendet)"
    & .\.venv\Scripts\python.exe server\app.py 2>&1 | Tee-Object -FilePath $Log -Append
    if ($LASTEXITCODE -eq 0) { break }
    $crashes++
    Write-Host "Backend beendet (Code $LASTEXITCODE). Neustart $crashes/5 in 10 s ..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}
