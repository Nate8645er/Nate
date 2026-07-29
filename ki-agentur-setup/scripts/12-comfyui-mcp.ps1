# =============================================================================
#  12-comfyui-mcp.ps1  -  ComfyUI MCP Server (joenorton/comfyui-mcp-server)
#  Bindet ComfyUI als MCP-Werkzeug in KI-Agenten (z.B. Claude Code) ein.
#  Erwartet lokal laufendes ComfyUI auf Port 8188; MCP-Server laeuft auf 9000.
# =============================================================================
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Banner 'ComfyUI MCP Server installieren'
Initialize-Workspace

$repo = Join-Path $script:ReposDir 'comfyui-mcp-server'
if (-not (Sync-GitRepo -Url 'https://github.com/joenorton/comfyui-mcp-server.git' -Dir $repo)) {
    Write-Log "ComfyUI-MCP-Repo konnte nicht bereitgestellt werden." 'ERROR'; exit 1
}

$venv = Join-Path $repo '.venv'
if (-not (Test-Path $venv)) {
    Write-Log "Erstelle virtuelle Umgebung ..." 'STEP'
    uv venv --python 3.12 $venv
}
$py = Join-Path $venv 'Scripts\python.exe'

$req = Join-Path $repo 'requirements.txt'
if (Test-Path $req) {
    Invoke-Retry -What 'pip mcp requirements' -Action {
        & uv pip install --python $py -r $req; if ($LASTEXITCODE -ne 0) { throw "requirements exit $LASTEXITCODE" }
    } | Out-Null
} else {
    Write-Log "Keine requirements.txt gefunden - installiere Basis-MCP-Abhaengigkeiten." 'WARN'
    & uv pip install --python $py mcp requests websockets | Out-Null
}

# Beispiel-Konfiguration zum Einbinden in Claude Code / andere MCP-Clients erzeugen
$mcpJson = Join-Path $script:ConfigDir 'claude-mcp-config.json'
$cfg = @{
    mcpServers = @{
        comfyui = @{
            command = $py
            args    = @((Join-Path $repo 'server.py'))
            env     = @{ COMFYUI_URL = "http://127.0.0.1:$($script:Ports.ComfyUI)" }
        }
    }
} | ConvertTo-Json -Depth 6
Set-Content -Path $mcpJson -Value $cfg -Encoding UTF8
Write-Log "MCP-Beispielkonfiguration geschrieben: $mcpJson" 'OK'
Write-Log "MCP-Server-Start via: start\start-comfyui-mcp.ps1  (http://127.0.0.1:$($script:Ports.ComfyUIMCP)/mcp)" 'OK'
Write-Log "Wichtig: Zuerst ComfyUI starten, dann den MCP-Server." 'INFO'
