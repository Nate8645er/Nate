# Builds the dashboard once. Needs Node.js 20+ (https://nodejs.org, LTS).
# Afterwards the backend serves it; no second server and no dev server needed.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path (Split-Path -Parent $PSScriptRoot) "web")
npm ci
npm run build
Write-Host "Fertig. node_modules kann danach geloescht werden, um Speicher zu sparen:"
Write-Host "  Remove-Item -Recurse -Force node_modules"
