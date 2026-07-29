# =============================================================================
#  20-browser-use.ps1  -  browser-use (offiziell: browser-use/browser-use, PyPI)
#  Automatisches Testen und Bedienen von Webseiten durch KI-Agenten
# =============================================================================
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Banner 'browser-use installieren'
Initialize-Workspace

# Eigene, isolierte Umgebung unter dem Workspace anlegen
$dir  = Join-Path $script:ReposDir 'browser-use'
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$venv = Join-Path $dir '.venv'
if (-not (Test-Path $venv)) {
    Write-Log "Erstelle virtuelle Umgebung (Python 3.12) ..." 'STEP'
    uv venv --python 3.12 $venv
}
$py = Join-Path $venv 'Scripts\python.exe'

Write-Log "Installiere browser-use ..." 'STEP'
Invoke-Retry -What 'pip browser-use' -Action {
    & uv pip install --python $py browser-use; if ($LASTEXITCODE -ne 0) { throw "pip exit $LASTEXITCODE" }
} | Out-Null

Write-Log "Installiere Playwright-Browser (Chromium) ..." 'STEP'
Invoke-Retry -What 'playwright install' -Action {
    & $py -m playwright install chromium; if ($LASTEXITCODE -ne 0) { throw "playwright exit $LASTEXITCODE" }
} | Out-Null

# Beispiel-Skript ablegen
$example = Join-Path $dir 'beispiel_agent.py'
if (-not (Test-Path $example)) {
@'
"""Minimalbeispiel: browser-use steuert einen Browser mit einem LLM.
Benoetigt einen API-Key in der Umgebung (z.B. OPENAI_API_KEY oder ueber OmniRoute)."""
import asyncio
from browser_use import Agent
from browser_use.llm import ChatOpenAI

async def main():
    agent = Agent(
        task="Oeffne example.com und fasse die Startseite in einem Satz zusammen.",
        llm=ChatOpenAI(model="gpt-4o-mini"),
    )
    result = await agent.run()
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
'@ | Set-Content -Path $example -Encoding UTF8
}

Write-Log "browser-use installiert. Beispiel: $example" 'OK'
Write-Log "API-Key setzen (z.B. \$env:OPENAI_API_KEY=... oder OmniRoute-Endpoint nutzen)." 'INFO'
