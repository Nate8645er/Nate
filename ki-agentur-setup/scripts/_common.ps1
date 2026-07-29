# =============================================================================
#  _common.ps1  -  Gemeinsame Hilfsfunktionen fuer die KI-Agentur-Installation
#  Wird von allen anderen Skripten per Dot-Sourcing eingebunden.
# =============================================================================

# --- Workspace-Wurzel (kann via Umgebungsvariable KI_AGENTUR_ROOT ueberschrieben werden) ---
if (-not $env:KI_AGENTUR_ROOT) {
    $script:Root = Join-Path $env:USERPROFILE 'KI-Agentur'
} else {
    $script:Root = $env:KI_AGENTUR_ROOT
}
$script:ReposDir  = Join-Path $script:Root 'repos'
$script:LogsDir   = Join-Path $script:Root 'logs'
$script:ConfigDir = Join-Path $script:Root 'config'

# --- Standard-Ports der Tools (zentral, damit alle Skripte konsistent bleiben) ---
$script:Ports = @{
    ComfyUI    = 8188
    ComfyUIMCP = 9000
    n8n        = 5678
    Metabase   = 3000
    OmniRoute  = 20128
    BoltDIY    = 5173
}

function Initialize-Workspace {
    foreach ($d in @($script:Root, $script:ReposDir, $script:LogsDir, $script:ConfigDir)) {
        if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
    }
}

# --- Logging -----------------------------------------------------------------
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('INFO','OK','WARN','ERROR','STEP')] [string]$Level = 'INFO'
    )
    $ts    = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $color = switch ($Level) {
        'OK'    { 'Green' }
        'WARN'  { 'Yellow' }
        'ERROR' { 'Red' }
        'STEP'  { 'Cyan' }
        default { 'Gray' }
    }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
    try {
        Initialize-Workspace
        Add-Content -Path (Join-Path $script:LogsDir 'install.log') -Value "[$ts] [$Level] $Message"
    } catch { }
}

# --- Vorhandensein eines Kommandos pruefen -----------------------------------
function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# --- Retry mit exponentiellem Backoff ----------------------------------------
function Invoke-Retry {
    param(
        [scriptblock]$Action,
        [int]$MaxAttempts = 4,
        [string]$What = 'Aktion'
    )
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            & $Action
            return $true
        } catch {
            $wait = [math]::Pow(2, $i)   # 2s, 4s, 8s, 16s
            Write-Log "$What fehlgeschlagen (Versuch $i/$MaxAttempts): $($_.Exception.Message)" 'WARN'
            if ($i -lt $MaxAttempts) { Start-Sleep -Seconds $wait }
        }
    }
    Write-Log "$What endgueltig fehlgeschlagen nach $MaxAttempts Versuchen." 'ERROR'
    return $false
}

# --- winget-Paket idempotent installieren ------------------------------------
function Install-WingetPackage {
    param(
        [Parameter(Mandatory)] [string]$Id,
        [string]$Name = $null,
        [string[]]$ExtraArgs = @()
    )
    if (-not $Name) { $Name = $Id }
    if (-not (Test-CommandExists 'winget')) {
        Write-Log "winget nicht gefunden. Bitte 'App Installer' aus dem Microsoft Store installieren." 'ERROR'
        return $false
    }
    # Bereits installiert?
    $installed = winget list --id $Id -e --accept-source-agreements 2>$null | Select-String -SimpleMatch $Id
    if ($installed) {
        Write-Log "$Name ist bereits installiert - ueberspringe." 'OK'
        return $true
    }
    Write-Log "Installiere $Name via winget ($Id) ..." 'STEP'
    $wingetArgs = @('install','--id',$Id,'-e','--source','winget',
              '--accept-package-agreements','--accept-source-agreements') + $ExtraArgs
    $ok = Invoke-Retry -What "winget install $Name" -Action { & winget @wingetArgs; if ($LASTEXITCODE -ne 0) { throw "winget exit $LASTEXITCODE" } }
    if ($ok) { Write-Log "$Name erfolgreich installiert." 'OK' }
    return $ok
}

# --- Git-Repo klonen oder aktualisieren (idempotent) -------------------------
function Sync-GitRepo {
    param(
        [Parameter(Mandatory)] [string]$Url,
        [Parameter(Mandatory)] [string]$Dir
    )
    if (Test-Path (Join-Path $Dir '.git')) {
        Write-Log "Aktualisiere vorhandenes Repo: $Dir" 'STEP'
        Invoke-Retry -What "git pull ($Dir)" -Action {
            git -C $Dir pull --ff-only; if ($LASTEXITCODE -ne 0) { throw "git pull exit $LASTEXITCODE" }
        } | Out-Null
    } else {
        Write-Log "Klone $Url -> $Dir" 'STEP'
        Invoke-Retry -What "git clone $Url" -Action {
            git clone --depth 1 $Url $Dir; if ($LASTEXITCODE -ne 0) { throw "git clone exit $LASTEXITCODE" }
        } | Out-Null
    }
    return (Test-Path (Join-Path $Dir '.git'))
}

# --- PATH nach Installationen im aktuellen Prozess auffrischen ----------------
function Update-SessionPath {
    $machine = [System.Environment]::GetEnvironmentVariable('Path','Machine')
    $user    = [System.Environment]::GetEnvironmentVariable('Path','User')
    $env:Path = ($machine, $user -join ';')
}

# --- Pruefen, ob eine NVIDIA-GPU vorhanden ist (fuer CUDA-Torch) --------------
function Test-NvidiaGpu {
    return (Test-CommandExists 'nvidia-smi')
}

# --- Banner ------------------------------------------------------------------
function Write-Banner {
    param([string]$Text)
    Write-Host ''
    Write-Host ('=' * 78) -ForegroundColor DarkCyan
    Write-Host "  $Text" -ForegroundColor White
    Write-Host ('=' * 78) -ForegroundColor DarkCyan
}
