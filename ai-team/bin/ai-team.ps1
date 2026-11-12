#!/usr/bin/env pwsh
# ai-team launcher für Windows/PowerShell. Nutzung:
#   .\ai-team\bin\ai-team.ps1 start
#   .\ai-team\bin\ai-team.ps1 council "Meine Aufgabe"
$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Core = Join-Path $ScriptDir '..\src\ai-team.mjs'

$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
  Write-Error 'ai-team: Node.js wird benoetigt (node nicht auf PATH gefunden). Installiere Node >=18.'
  exit 1
}
& node $Core @args
exit $LASTEXITCODE
