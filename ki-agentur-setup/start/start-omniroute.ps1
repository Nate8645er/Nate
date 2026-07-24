# Startet OmniRoute (http://127.0.0.1:20128 - Dashboard + OpenAI-kompatible API)
. (Join-Path $PSScriptRoot '..\scripts\_common.ps1')
if (-not (Test-CommandExists 'omniroute')) { Write-Log "OmniRoute nicht im PATH. Erst install.ps1 -Only omniroute ausfuehren / neues Terminal." 'ERROR'; exit 1 }
$env:PORT = $script:Ports.OmniRoute
Write-Log "Starte OmniRoute auf Port $($script:Ports.OmniRoute) ..." 'STEP'
Write-Log "API-Endpoint fuer andere Tools: http://localhost:$($script:Ports.OmniRoute)/v1  (Modell: auto)" 'INFO'
omniroute
