# Startet den bolt.diy Dev-Server (http://localhost:5173)
. (Join-Path $PSScriptRoot '..\scripts\_common.ps1')
$repo = Join-Path $script:ReposDir 'bolt.diy'
if (-not (Test-Path (Join-Path $repo 'package.json'))) { Write-Log "bolt.diy nicht installiert. Erst install.ps1 -Only bolt-diy ausfuehren." 'ERROR'; exit 1 }
if (-not (Test-CommandExists 'pnpm')) { Write-Log "pnpm fehlt." 'ERROR'; exit 1 }
Write-Log "Starte bolt.diy Dev-Server auf Port $($script:Ports.BoltDIY) ..." 'STEP'
Push-Location $repo
try { pnpm run dev } finally { Pop-Location }
