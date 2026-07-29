# Startet ComfyUI (http://127.0.0.1:8188)
. (Join-Path $PSScriptRoot '..\scripts\_common.ps1')
$repo = Join-Path $script:ReposDir 'ComfyUI'
$py   = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) { Write-Log "ComfyUI nicht installiert. Erst install.ps1 -Only comfyui ausfuehren." 'ERROR'; exit 1 }
Write-Log "Starte ComfyUI auf Port $($script:Ports.ComfyUI) ..." 'STEP'
Push-Location $repo
try { & $py main.py --port $script:Ports.ComfyUI } finally { Pop-Location }
