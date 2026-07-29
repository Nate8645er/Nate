# Startet n8n (http://127.0.0.1:5678)
. (Join-Path $PSScriptRoot '..\scripts\_common.ps1')
if (-not (Test-CommandExists 'n8n')) { Write-Log "n8n nicht im PATH. Erst install.ps1 -Only n8n ausfuehren / neues Terminal." 'ERROR'; exit 1 }
$env:N8N_USER_FOLDER = Join-Path $script:Root 'n8n-data'
$env:N8N_PORT        = $script:Ports.n8n
Write-Log "Starte n8n auf Port $($script:Ports.n8n) (Daten: $($env:N8N_USER_FOLDER)) ..." 'STEP'
n8n start
