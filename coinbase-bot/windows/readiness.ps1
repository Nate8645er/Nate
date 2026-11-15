# Runs the LIVE_READINESS_CHECK with the keys from .env. Sends no order.
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (Test-Path ".env") {
    Get-Content ".env" | Where-Object { $_ -match "^\s*[^#\s][^=]*=" } | ForEach-Object {
        $name, $value = $_ -split "=", 2
        if ($value.Trim()) { [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process") }
    }
}
& .\.venv\Scripts\python.exe scripts\readiness_check.py
