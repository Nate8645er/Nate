# =============================================================================
#  00-prerequisites.ps1  -  Installiert alle Grundvoraussetzungen via winget
#  Git, Python, Node.js, npm, uv, Docker Desktop, Java (Temurin), VS Build Tools, pnpm
# =============================================================================
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Banner 'Schritt 0: Grundvoraussetzungen installieren'
Initialize-Workspace

# --- winget selbst pruefen ---------------------------------------------------
if (-not (Test-CommandExists 'winget')) {
    Write-Log "winget (App Installer) fehlt. Bitte aus dem Microsoft Store installieren und Skript erneut starten." 'ERROR'
    Write-Log "Store-Link: https://apps.microsoft.com/detail/9nblggh4nns1" 'INFO'
    exit 1
}

# --- Kernpakete --------------------------------------------------------------
Install-WingetPackage -Id 'Git.Git'                 -Name 'Git'
Install-WingetPackage -Id 'Python.Python.3.12'      -Name 'Python 3.12'
Install-WingetPackage -Id 'OpenJS.NodeJS.LTS'       -Name 'Node.js LTS (inkl. npm)'
Install-WingetPackage -Id 'astral-sh.uv'            -Name 'uv (Python-Paketmanager)'
Install-WingetPackage -Id 'EclipseAdoptium.Temurin.21.JDK' -Name 'Java (Temurin 21 JDK)'

# Docker Desktop (grosser Download; benoetigt spaeter Neustart + WSL2)
Install-WingetPackage -Id 'Docker.DockerDesktop'    -Name 'Docker Desktop'

# Visual Studio Build Tools inkl. C++-Workload (fuer viele Python-Pakete noetig)
Install-WingetPackage -Id 'Microsoft.VisualStudio.2022.BuildTools' -Name 'VS 2022 Build Tools (C++)' `
    -ExtraArgs @('--override','--wait --quiet --norestart --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended')

# --- PATH auffrischen, damit die neuen Tools sofort nutzbar sind -------------
Update-SessionPath

# --- pnpm (fuer bolt.diy) via corepack/npm ----------------------------------
if (Test-CommandExists 'npm') {
    if (-not (Test-CommandExists 'pnpm')) {
        Write-Log "Installiere pnpm ..." 'STEP'
        try { corepack enable pnpm 2>$null } catch { }
        if (-not (Test-CommandExists 'pnpm')) {
            Invoke-Retry -What 'npm i -g pnpm' -Action { npm install -g pnpm; if ($LASTEXITCODE -ne 0) { throw "npm exit $LASTEXITCODE" } } | Out-Null
        }
        Update-SessionPath
    } else { Write-Log "pnpm bereits vorhanden." 'OK' }
} else {
    Write-Log "npm noch nicht im PATH - bitte neues Terminal oeffnen und Skript ggf. erneut ausfuehren." 'WARN'
}

# --- Kurzbericht -------------------------------------------------------------
Write-Banner 'Voraussetzungen - Status'
foreach ($t in 'git','python','node','npm','uv','java','docker','pnpm') {
    if (Test-CommandExists $t) {
        $ver = (& $t --version 2>$null | Select-Object -First 1)
        Write-Log ("{0,-8} OK   {1}" -f $t, $ver) 'OK'
    } else {
        Write-Log ("{0,-8} FEHLT (evtl. neues Terminal noetig oder Neustart nach Docker/Build-Tools)" -f $t) 'WARN'
    }
}
Write-Log "Hinweis: Nach der Docker-Desktop-Installation ist meist ein Windows-Neustart noetig (WSL2)." 'INFO'
