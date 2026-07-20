# =============================================================================
#  10-comfyui.ps1  -  ComfyUI (offiziell: comfyanonymous/ComfyUI)
#  KI-Bilder, Logos, Banner, Produktbilder
# =============================================================================
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Banner 'ComfyUI installieren'
Initialize-Workspace

$repo = Join-Path $script:ReposDir 'ComfyUI'
if (-not (Sync-GitRepo -Url 'https://github.com/comfyanonymous/ComfyUI.git' -Dir $repo)) {
    Write-Log "ComfyUI-Repo konnte nicht bereitgestellt werden." 'ERROR'; exit 1
}

# --- Virtuelle Umgebung mit uv anlegen ---------------------------------------
$venv = Join-Path $repo '.venv'
if (-not (Test-Path $venv)) {
    Write-Log "Erstelle virtuelle Umgebung (Python 3.12) ..." 'STEP'
    uv venv --python 3.12 $venv
}
$py = Join-Path $venv 'Scripts\python.exe'

# --- PyTorch installieren (CUDA falls NVIDIA-GPU, sonst CPU) ------------------
if (Test-NvidiaGpu) {
    Write-Log "NVIDIA-GPU erkannt - installiere PyTorch mit CUDA 12.1." 'STEP'
    Invoke-Retry -What 'pip torch cuda' -Action {
        & uv pip install --python $py torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
        if ($LASTEXITCODE -ne 0) { throw "torch install exit $LASTEXITCODE" }
    } | Out-Null
} else {
    Write-Log "Keine NVIDIA-GPU erkannt - installiere PyTorch (CPU). Bildgenerierung ist dann langsam." 'WARN'
    Invoke-Retry -What 'pip torch cpu' -Action {
        & uv pip install --python $py torch torchvision torchaudio
        if ($LASTEXITCODE -ne 0) { throw "torch install exit $LASTEXITCODE" }
    } | Out-Null
}

# --- ComfyUI-Abhaengigkeiten -------------------------------------------------
Write-Log "Installiere ComfyUI-Requirements ..." 'STEP'
Invoke-Retry -What 'pip requirements' -Action {
    & uv pip install --python $py -r (Join-Path $repo 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw "requirements exit $LASTEXITCODE" }
} | Out-Null

Write-Log "ComfyUI installiert. Start via: start\start-comfyui.ps1  (http://127.0.0.1:$($script:Ports.ComfyUI))" 'OK'
Write-Log "Hinweis: Checkpoints/Modelle nach $repo\models\checkpoints legen (z.B. SDXL, Flux)." 'INFO'
