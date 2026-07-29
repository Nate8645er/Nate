# =============================================================================
#  50-metabase.ps1  -  Metabase (offiziell: metabase/metabase)
#  Dashboards und Datenanalysen. Laeuft als Java-JAR (benoetigt Java 21).
# =============================================================================
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '_common.ps1')

Write-Banner 'Metabase installieren'
Initialize-Workspace

$dir = Join-Path $script:Root 'metabase'
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
$jar = Join-Path $dir 'metabase.jar'

if (-not (Test-CommandExists 'java')) {
    Write-Log "Java fehlt. Bitte 00-prerequisites.ps1 ausfuehren (Temurin 21) / neues Terminal oeffnen." 'ERROR'; exit 1
}

if (Test-Path $jar) {
    Write-Log "metabase.jar bereits vorhanden - ueberspringe Download." 'OK'
} else {
    Write-Log "Lade offizielle metabase.jar ..." 'STEP'
    $url = 'https://downloads.metabase.com/latest/metabase.jar'
    Invoke-Retry -What 'download metabase.jar' -Action {
        Invoke-WebRequest -Uri $url -OutFile $jar -UseBasicParsing
        if (-not (Test-Path $jar)) { throw "Download fehlgeschlagen" }
    } | Out-Null
}

if (Test-Path $jar) {
    Write-Log "Metabase installiert: $jar" 'OK'
    Write-Log "Start via: start\start-metabase.ps1  (http://127.0.0.1:$($script:Ports.Metabase))" 'OK'
    Write-Log "Alternativ Docker: docker run -d -p 3000:3000 --name metabase metabase/metabase" 'INFO'
} else {
    Write-Log "Metabase-JAR konnte nicht bereitgestellt werden." 'ERROR'
}
