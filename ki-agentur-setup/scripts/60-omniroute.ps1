# =============================================================================
#  60-omniroute.ps1  -  OmniRoute (offiziell: diegosouzapw/OmniRoute, npm: omniroute)
#  KI-Gateway: ein OpenAI-kompatibler Endpoint fuer viele Modelle/Provider.
#  Dashboard + API laufen auf Port 20128.
# =============================================================================
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Banner 'OmniRoute installieren'
Initialize-Workspace

if (-not (Test-CommandExists 'npm')) {
    Write-Log "npm fehlt. Bitte 00-prerequisites.ps1 ausfuehren / neues Terminal oeffnen." 'ERROR'; exit 1
}

Write-Log "Installiere omniroute global via npm ..." 'STEP'
Invoke-Retry -What 'npm i -g omniroute' -Action {
    npm install -g omniroute; if ($LASTEXITCODE -ne 0) { throw "npm exit $LASTEXITCODE" }
} | Out-Null
Update-SessionPath

if (Test-CommandExists 'omniroute') {
    Write-Log "OmniRoute installiert." 'OK'
    Write-Log "Start via: start\start-omniroute.ps1  (http://127.0.0.1:$($script:Ports.OmniRoute))" 'OK'
    Write-Log "Danach im Dashboard einen Provider verbinden; Endpoint fuer andere Tools: http://localhost:$($script:Ports.OmniRoute)/v1" 'INFO'
} else {
    Write-Log "omniroute-Befehl nicht im PATH - neues Terminal oeffnen." 'WARN'
    Write-Log "Docker-Alternative: docker run -d --name omniroute -p 20128:20128 -v omniroute-data:/app/data diegosouzapw/omniroute:latest" 'INFO'
}
