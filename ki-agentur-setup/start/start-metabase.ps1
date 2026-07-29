# Startet Metabase (http://127.0.0.1:3000)
. (Join-Path $PSScriptRoot '..\scripts\_common.ps1')
$jar = Join-Path $script:Root 'metabase\metabase.jar'
if (-not (Test-Path $jar)) { Write-Log "Metabase nicht installiert. Erst install.ps1 -Only metabase ausfuehren." 'ERROR'; exit 1 }
if (-not (Test-CommandExists 'java')) { Write-Log "Java fehlt (Temurin 21)." 'ERROR'; exit 1 }
$env:MB_JETTY_PORT = $script:Ports.Metabase
$env:MB_DB_FILE    = Join-Path $script:Root 'metabase\metabase.db'
Write-Log "Starte Metabase auf Port $($script:Ports.Metabase) (Erststart dauert 1-2 Min.) ..." 'STEP'
java -jar $jar
