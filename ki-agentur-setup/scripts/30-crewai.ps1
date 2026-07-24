# =============================================================================
#  30-crewai.ps1  -  CrewAI (offiziell: crewAIInc/crewAI, PyPI: crewai)
#  Multi-Agenten-Systeme und komplexe Arbeitsablaeufe
# =============================================================================
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Banner 'CrewAI installieren'
Initialize-Workspace

# CrewAI als isoliertes uv-Tool -> globaler "crewai"-Befehl
Write-Log "Installiere crewai (inkl. tools) via uv tool ..." 'STEP'
$ok = Invoke-Retry -What 'uv tool install crewai' -Action {
    uv tool install "crewai[tools]" --force; if ($LASTEXITCODE -ne 0) { throw "uv tool exit $LASTEXITCODE" }
}
if (-not $ok) {
    Write-Log "uv-Tool fehlgeschlagen, versuche pip in dedizierter venv ..." 'WARN'
    $dir  = Join-Path $script:ReposDir 'crewai'
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $venv = Join-Path $dir '.venv'
    if (-not (Test-Path $venv)) { uv venv --python 3.12 $venv }
    $py = Join-Path $venv 'Scripts\python.exe'
    Invoke-Retry -What 'pip crewai' -Action { & uv pip install --python $py "crewai[tools]"; if ($LASTEXITCODE -ne 0) { throw "pip exit $LASTEXITCODE" } } | Out-Null
}
Update-SessionPath

if (Test-CommandExists 'crewai') {
    Write-Log ("crewai OK: " + (crewai version 2>$null)) 'OK'
    Write-Log "Neues Multi-Agenten-Projekt: 'crewai create crew <name>' im gewuenschten Ordner." 'INFO'
} else {
    Write-Log "crewai-Befehl (noch) nicht im PATH - neues Terminal oeffnen." 'WARN'
}
Write-Log "LLM-Keys via .env konfigurieren (OPENAI_API_KEY / ANTHROPIC_API_KEY oder OmniRoute)." 'INFO'
