# =============================================================================
#  install.ps1  -  Master-Bootstrap der KI-Agentur-Umgebung
# -----------------------------------------------------------------------------
#  Installiert Voraussetzungen + alle 9 Tools und verifiziert am Ende.
#
#  Nutzung (PowerShell als normaler Benutzer; winget muss vorhanden sein):
#      pwsh -ExecutionPolicy Bypass -File .\install.ps1
#
#  Optionen:
#      -Root <Pfad>       Ziel-Workspace (Standard: %USERPROFILE%\KI-Agentur)
#      -SkipPrereqs       Schritt 0 (Voraussetzungen) ueberspringen
#      -Only a,b,c        Nur bestimmte Tools installieren (siehe $All unten)
#      -Force             (an Skripte durchgereicht wo relevant)
#
#  Beispiel: nur ComfyUI + n8n:
#      pwsh -File .\install.ps1 -Only comfyui,n8n
# =============================================================================
[CmdletBinding()]
param(
    [string]$Root,
    [switch]$SkipPrereqs,
    [string[]]$Only,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'

if ($Root) { $env:KI_AGENTUR_ROOT = $Root }
. (Join-Path $PSScriptRoot 'scripts\_common.ps1')
Initialize-Workspace

Write-Banner 'KI-AGENTUR - Vollautomatische Einrichtung'
Write-Log "Workspace: $script:Root" 'INFO'

# Reihenfolge + Zuordnung Kurzname -> Skript
$All = [ordered]@{
    'comfyui'     = '10-comfyui.ps1'
    'comfy-cli'   = '11-comfy-cli.ps1'
    'comfyui-mcp' = '12-comfyui-mcp.ps1'
    'browser-use' = '20-browser-use.ps1'
    'crewai'      = '30-crewai.ps1'
    'n8n'         = '40-n8n.ps1'
    'metabase'    = '50-metabase.ps1'
    'omniroute'   = '60-omniroute.ps1'
    'bolt-diy'    = '70-bolt-diy.ps1'
}

# Schritt 0: Voraussetzungen
if (-not $SkipPrereqs) {
    & (Join-Path $PSScriptRoot 'scripts\00-prerequisites.ps1')
    Update-SessionPath
} else {
    Write-Log "Voraussetzungen uebersprungen (-SkipPrereqs)." 'WARN'
}

# Auswahl bestimmen
$selected = if ($Only) { $All.GetEnumerator() | Where-Object { $Only -contains $_.Key } }
            else       { $All.GetEnumerator() }

$results = @()
foreach ($entry in $selected) {
    $name   = $entry.Key
    $script = Join-Path $PSScriptRoot ('scripts\' + $entry.Value)
    Write-Banner "Tool: $name"
    try {
        & $script
        $results += [pscustomobject]@{ Tool = $name; Ergebnis = 'OK' }
    } catch {
        Write-Log "Fehler bei $name : $($_.Exception.Message)" 'ERROR'
        $results += [pscustomobject]@{ Tool = $name; Ergebnis = 'FEHLER' }
    }
}

# Abschluss-Verifizierung
& (Join-Path $PSScriptRoot 'scripts\99-verify.ps1')

Write-Banner 'Zusammenfassung Installation'
$results | Format-Table -AutoSize
Write-Log "Fertig. Dienste starten mit den Skripten im Ordner 'start' (z.B. start\start-all.ps1)." 'OK'
Write-Log "Bei fehlenden Befehlen: neues Terminal oeffnen (PATH) bzw. nach Docker-Installation Windows neu starten." 'INFO'
