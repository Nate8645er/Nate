# =============================================================================
#  70-bolt-diy.ps1  -  bolt.diy (offiziell: stackblitz-labs/bolt.diy)
#  Schnelle Erstellung von Webanwendungen per KI. Dev-Server auf Port 5173.
# =============================================================================
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Banner 'bolt.diy installieren'
Initialize-Workspace

$repo = Join-Path $script:ReposDir 'bolt.diy'
if (-not (Sync-GitRepo -Url 'https://github.com/stackblitz-labs/bolt.diy.git' -Dir $repo)) {
    Write-Log "bolt.diy-Repo konnte nicht bereitgestellt werden." 'ERROR'; exit 1
}

if (-not (Test-CommandExists 'pnpm')) {
    Write-Log "pnpm fehlt. Installiere pnpm ..." 'STEP'
    try { corepack enable pnpm 2>$null } catch { }
    if (-not (Test-CommandExists 'pnpm')) { npm install -g pnpm | Out-Null }
    Update-SessionPath
}

Write-Log "Installiere bolt.diy-Abhaengigkeiten (pnpm install) ..." 'STEP'
Push-Location $repo
try {
    Invoke-Retry -What 'pnpm install' -Action { pnpm install; if ($LASTEXITCODE -ne 0) { throw "pnpm exit $LASTEXITCODE" } } | Out-Null

    # .env aus Vorlage anlegen, falls vorhanden
    foreach ($envFile in '.env.local','.env') {
        $tpl = Join-Path $repo '.env.example'
        $dst = Join-Path $repo $envFile
        if ((Test-Path $tpl) -and (-not (Test-Path $dst))) {
            Copy-Item $tpl $dst
            Write-Log "Angelegt: $envFile (bitte API-Keys eintragen)." 'INFO'
        }
    }
} finally { Pop-Location }

Write-Log "bolt.diy installiert. Start via: start\start-bolt-diy.ps1  (http://localhost:$($script:Ports.BoltDIY))" 'OK'
Write-Log "API-Keys in $repo\.env.local eintragen oder ueber die Oberflaeche setzen." 'INFO'
