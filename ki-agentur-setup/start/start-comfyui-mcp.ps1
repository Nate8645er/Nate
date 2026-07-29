# Startet den ComfyUI-MCP-Server (http://127.0.0.1:9000/mcp)
# Voraussetzung: ComfyUI laeuft bereits (start-comfyui.ps1).
. (Join-Path $PSScriptRoot '..\scripts\_common.ps1')
$repo = Join-Path $script:ReposDir 'comfyui-mcp-server'
$py   = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) { Write-Log "ComfyUI-MCP nicht installiert. Erst install.ps1 -Only comfyui-mcp ausfuehren." 'ERROR'; exit 1 }
$env:COMFYUI_URL = "http://127.0.0.1:$($script:Ports.ComfyUI)"
Write-Log "Starte ComfyUI-MCP-Server auf Port $($script:Ports.ComfyUIMCP) ..." 'STEP'
Push-Location $repo
try { & $py server.py } finally { Pop-Location }
