# =============================================================================
#  99-verify.ps1  -  Prueft, ob alle Tools installiert und erreichbar sind
# =============================================================================
$ErrorActionPreference = 'Continue'
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Banner 'Verifizierung: Installation & Erreichbarkeit'
Update-SessionPath

$rows = @()

function Add-Check {
    param([string]$Name, [bool]$Ok, [string]$Detail)
    $script:rows += [pscustomobject]@{ Tool = $Name; Status = ($(if ($Ok) {'OK'} else {'FEHLT'})); Detail = $Detail }
}

# --- Voraussetzungen ---------------------------------------------------------
foreach ($t in 'git','python','node','npm','uv','java','pnpm','docker') {
    $ok = Test-CommandExists $t
    Add-Check $t $ok ($(if ($ok) { (& $t --version 2>$null | Select-Object -First 1) } else { 'nicht im PATH' }))
}

# --- Tool-Befehle ------------------------------------------------------------
Add-Check 'comfy (CLI)'  (Test-CommandExists 'comfy')     'comfy-cli'
Add-Check 'crewai'       (Test-CommandExists 'crewai')    'CrewAI-CLI'
Add-Check 'n8n'          (Test-CommandExists 'n8n')       'n8n-CLI'
Add-Check 'omniroute'    (Test-CommandExists 'omniroute') 'OmniRoute-CLI'

# --- Repos / Dateien ---------------------------------------------------------
$checks = @{
    'ComfyUI (Repo)'      = (Join-Path $script:ReposDir 'ComfyUI\main.py')
    'ComfyUI-MCP (Repo)'  = (Join-Path $script:ReposDir 'comfyui-mcp-server\server.py')
    'browser-use (venv)'  = (Join-Path $script:ReposDir 'browser-use\.venv\Scripts\python.exe')
    'bolt.diy (Repo)'     = (Join-Path $script:ReposDir 'bolt.diy\package.json')
    'Metabase (JAR)'      = (Join-Path $script:Root 'metabase\metabase.jar')
}
foreach ($k in $checks.Keys) { Add-Check $k (Test-Path $checks[$k]) $checks[$k] }

# --- Laufende Ports pruefen (falls Dienste bereits gestartet) ----------------
function Test-Port { param([int]$Port)
    try { return (Test-NetConnection -ComputerName '127.0.0.1' -Port $Port -WarningAction SilentlyContinue).TcpTestSucceeded }
    catch { return $false }
}
foreach ($p in $script:Ports.GetEnumerator()) {
    $up = Test-Port $p.Value
    Add-Check ("Port $($p.Key)") $up "127.0.0.1:$($p.Value)$(if(-not $up){' (Dienst nicht gestartet)'})"
}

$rows | Format-Table -AutoSize
$fail = ($rows | Where-Object { $_.Status -eq 'FEHLT' -and $_.Tool -notlike 'Port*' }).Count
if ($fail -eq 0) { Write-Log "Alle Kern-Checks bestanden." 'OK' }
else { Write-Log "$fail Komponente(n) fehlen. Ggf. neues Terminal oeffnen oder betroffenes Skript erneut ausfuehren." 'WARN' }
Write-Log "Ports zeigen 'FEHLT', solange der jeweilige Dienst nicht laeuft - das ist normal." 'INFO'
