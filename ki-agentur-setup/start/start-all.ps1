# =============================================================================
#  start-all.ps1  -  Startet alle Dauerdienste in eigenen Fenstern
#  (ComfyUI, ComfyUI-MCP, n8n, Metabase, OmniRoute, bolt.diy)
#  browser-use / CrewAI / Comfy CLI sind bedarfsgesteuerte Werkzeuge und
#  werden hier NICHT als Dauerdienst gestartet.
# =============================================================================
. (Join-Path $PSScriptRoot '..\scripts\_common.ps1')

function Start-Service {
    param([string]$Title, [string]$Script)
    $path = Join-Path $PSScriptRoot $Script
    if (-not (Test-Path $path)) { Write-Log "Startskript fehlt: $Script" 'WARN'; return }
    Write-Log "Starte $Title ..." 'STEP'
    Start-Process -FilePath 'powershell.exe' `
        -ArgumentList @('-NoExit','-ExecutionPolicy','Bypass','-File',$path) `
        -WindowStyle Normal
    Start-Sleep -Seconds 2
}

Write-Banner 'Starte alle KI-Agentur-Dienste'
Start-Service 'ComfyUI'        'start-comfyui.ps1'
Start-Sleep -Seconds 6   # ComfyUI zuerst hochfahren lassen, bevor der MCP-Server verbindet
Start-Service 'ComfyUI-MCP'    'start-comfyui-mcp.ps1'
Start-Service 'n8n'            'start-n8n.ps1'
Start-Service 'Metabase'       'start-metabase.ps1'
Start-Service 'OmniRoute'      'start-omniroute.ps1'
Start-Service 'bolt.diy'       'start-bolt-diy.ps1'

Write-Banner 'Dienste gestartet - URLs'
Write-Host "  ComfyUI      http://127.0.0.1:$($script:Ports.ComfyUI)"
Write-Host "  ComfyUI-MCP  http://127.0.0.1:$($script:Ports.ComfyUIMCP)/mcp"
Write-Host "  n8n          http://127.0.0.1:$($script:Ports.n8n)"
Write-Host "  Metabase     http://127.0.0.1:$($script:Ports.Metabase)"
Write-Host "  OmniRoute    http://127.0.0.1:$($script:Ports.OmniRoute)"
Write-Host "  bolt.diy     http://localhost:$($script:Ports.BoltDIY)"
Write-Log "Jeder Dienst laeuft in einem eigenen Fenster. Zum Stoppen das jeweilige Fenster schliessen." 'INFO'
