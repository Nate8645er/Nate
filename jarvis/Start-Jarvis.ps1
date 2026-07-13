# JARVIS HyperScale - Windows-Starter
# Installiert die Python-Abhaengigkeiten (einmalig) und startet das Dashboard.
# Aufruf:  powershell -ExecutionPolicy Bypass -File .\Start-Jarvis.ps1 [-Demo]
param([switch]$Demo)

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
& "$venv\Scripts\python.exe" -m pip install -q -r (Join-Path $here 'requirements.txt')

$env:PYTHONPATH = $repo
$args = @('-m', 'jarvis.run')
if ($Demo) { $args += '--demo' }

Write-Host ""
Write-Host "JARVIS startet - Dashboard: http://127.0.0.1:8787" -ForegroundColor Green
Start-Process "http://127.0.0.1:8787"
& "$venv\Scripts\python.exe" @args
