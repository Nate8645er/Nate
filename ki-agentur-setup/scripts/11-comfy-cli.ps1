# =============================================================================
#  11-comfy-cli.ps1  -  Comfy CLI (offiziell: Comfy-Org/comfy-cli, PyPI: comfy-cli)
#  Automatisierung / Steuerung von ComfyUI ueber die Kommandozeile
# =============================================================================
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Banner 'Comfy CLI installieren'
Initialize-Workspace

# Als isoliertes uv-Tool installieren -> globaler Befehl "comfy"
Write-Log "Installiere comfy-cli via uv tool ..." 'STEP'
$ok = Invoke-Retry -What 'uv tool install comfy-cli' -Action {
    uv tool install comfy-cli --force; if ($LASTEXITCODE -ne 0) { throw "uv tool exit $LASTEXITCODE" }
}
if (-not $ok) {
    Write-Log "uv-Tool-Installation fehlgeschlagen, versuche pip ..." 'WARN'
    Invoke-Retry -What 'pip comfy-cli' -Action { pip install --upgrade comfy-cli; if ($LASTEXITCODE -ne 0) { throw "pip exit $LASTEXITCODE" } } | Out-Null
}
Update-SessionPath

# Comfy CLI auf die bereits installierte ComfyUI-Instanz zeigen lassen
$comfyRepo = Join-Path $script:ReposDir 'ComfyUI'
if ((Test-CommandExists 'comfy') -and (Test-Path $comfyRepo)) {
    try {
        Write-Log "Setze Standard-ComfyUI-Pfad fuer comfy-cli auf $comfyRepo" 'STEP'
        comfy --skip-prompt set-default $comfyRepo 2>$null
    } catch { Write-Log "Konnte Standardpfad nicht setzen (nicht kritisch)." 'WARN' }
}

if (Test-CommandExists 'comfy') {
    Write-Log ("comfy-cli OK: " + (comfy --version 2>$null)) 'OK'
    Write-Log "Beispiel: 'comfy launch' startet ComfyUI, 'comfy node install <name>' installiert Custom Nodes." 'INFO'
} else {
    Write-Log "comfy-Befehl nicht im PATH - neues Terminal oeffnen." 'WARN'
}
