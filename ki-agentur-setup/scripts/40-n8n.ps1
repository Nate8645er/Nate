# =============================================================================
#  40-n8n.ps1  -  n8n (offiziell: n8n-io/n8n, npm-Paket: n8n)
#  Automatisierungen und Workflows
# =============================================================================
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Banner 'n8n installieren'
Initialize-Workspace

if (-not (Test-CommandExists 'npm')) {
    Write-Log "npm fehlt. Bitte zuerst 00-prerequisites.ps1 ausfuehren / neues Terminal oeffnen." 'ERROR'; exit 1
}

Write-Log "Installiere n8n global via npm ..." 'STEP'
Invoke-Retry -What 'npm i -g n8n' -Action {
    npm install -g n8n; if ($LASTEXITCODE -ne 0) { throw "npm exit $LASTEXITCODE" }
} | Out-Null
Update-SessionPath

# Eigenes Daten-/Konfigverzeichnis fuer n8n
$n8nData = Join-Path $script:Root 'n8n-data'
if (-not (Test-Path $n8nData)) { New-Item -ItemType Directory -Path $n8nData -Force | Out-Null }

if (Test-CommandExists 'n8n') {
    Write-Log ("n8n OK: " + (n8n --version 2>$null)) 'OK'
    Write-Log "Start via: start\start-n8n.ps1  (http://127.0.0.1:$($script:Ports.n8n))" 'OK'
} else {
    Write-Log "n8n-Befehl nicht im PATH - neues Terminal oeffnen. Alternativ Docker-Variante nutzen." 'WARN'
    Write-Log "Docker-Alternative: docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n" 'INFO'
}
