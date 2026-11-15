# System diagnosis and resource check. Read-only: changes nothing.
#   powershell -ExecutionPolicy Bypass -File windows\diagnose.ps1
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
function Line($k, $v) { "{0,-34} {1}" -f $k, $v }

"=== HyperGrok Diagnose ==="
$os = Get-CimInstance Win32_OperatingSystem
Line "Windows" $os.Caption
Line "RAM frei / gesamt (GB)" ("{0:N1} / {1:N1}" -f ($os.FreePhysicalMemory / 1MB), ($os.TotalVisibleMemorySize / 1MB))
$drive = Get-PSDrive -Name (Get-Location).Drive.Name
Line "Speicher frei (GB)" ("{0:N1}" -f ($drive.Free / 1GB))
Line "Python" ((python --version) 2>&1)
Line "Node" ((node --version) 2>&1)
Line ".venv vorhanden" (Test-Path ".venv")
Line "Dashboard gebaut (web\dist)" (Test-Path "web\dist\index.html")
Line ".env vorhanden" (Test-Path ".env")
Line "Not-Aus-Datei" (Test-Path "state\emergency_stop.json")
if (Test-Path "state\emergency_stop.json") { Line "  Inhalt" (Get-Content "state\emergency_stop.json" -Raw) }
Line "Projektgroesse (MB)" ("{0:N0}" -f ((Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum / 1MB))
if (Test-Path "logs") { Line "Logs (MB)" ("{0:N1}" -f ((Get-ChildItem logs -File | Measure-Object Length -Sum).Sum / 1MB)) }

$listen = Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue
Line "Port 8787 belegt" ([bool]$listen)
if ($listen) {
    Line "  nur lokal (127.0.0.1)" ($listen.LocalAddress -contains "127.0.0.1")
    $proc = Get-Process -Id $listen[0].OwningProcess
    Line "  Backend RAM (MB)" ("{0:N0}" -f ($proc.WorkingSet64 / 1MB))
    try { Line "  /api/health" ((Invoke-RestMethod "http://127.0.0.1:8787/api/health" -TimeoutSec 5) | ConvertTo-Json -Compress) }
    catch { Line "  /api/health" "NICHT ERREICHBAR" }
}
if (($os.FreePhysicalMemory / 1MB) -lt 1) { Write-Host "WARNUNG: weniger als 1 GB RAM frei." -ForegroundColor Yellow }
if (($drive.Free / 1GB) -lt 2) { Write-Host "WARNUNG: weniger als 2 GB Speicher frei." -ForegroundColor Yellow }
