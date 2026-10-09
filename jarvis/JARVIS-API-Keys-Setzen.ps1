# ============================================================================
#  JARVIS API-Keys setzen (PowerShell)
# ============================================================================
#  Trägt deine API-Keys dauerhaft als Windows-Umgebungsvariablen ein (setx).
#  JARVIS verbindet sich beim naechsten Start automatisch damit — ohne Klicken.
#
#  Ausfuehren:  Rechtsklick auf diese Datei -> "Mit PowerShell ausfuehren"
#  oder im Terminal:
#     powershell -ExecutionPolicy Bypass -File .\JARVIS-API-Keys-Setzen.ps1
#
#  Jeden Key kannst du ueberspringen (einfach Enter druecken).
# ============================================================================

Write-Host ""
Write-Host "  JARVIS API-Keys eintragen" -ForegroundColor Magenta
Write-Host "  =========================" -ForegroundColor Magenta
Write-Host "  Einfach den jeweiligen Key einfuegen und Enter druecken."
Write-Host "  Leer lassen (nur Enter) = ueberspringen / unveraendert lassen."
Write-Host ""

function Set-Key($name, $label, $hint) {
    Write-Host ""
    Write-Host "  $label" -ForegroundColor Cyan
    if ($hint) { Write-Host "    $hint" -ForegroundColor DarkGray }
    $val = Read-Host "    $name"
    if ($val.Trim().Length -gt 0) {
        setx $name $val.Trim() | Out-Null
        Write-Host "    [OK] $name gesetzt." -ForegroundColor Green
    } else {
        Write-Host "    (uebersprungen)" -ForegroundColor DarkGray
    }
}

# 1) Fable 5 / Claude (Anthropic)
Set-Key "ANTHROPIC_API_KEY" "Fable 5 / Claude  (Anthropic)" "Key von console.anthropic.com  (Format sk-ant-...)"

# 2) Viele Modelle (OpenRouter)
Set-Key "OPENROUTER_API_KEY" "Viele Modelle  (OpenRouter, 32 Modelle)" "Key von openrouter.ai/keys  (Format sk-or-...)"

# 3) Echte Stimme (ElevenLabs)
Set-Key "ELEVENLABS_API_KEY" "Echte Stimme  (ElevenLabs)" "Key von elevenlabs.io"

# 4) Stimm-ID (Standard ist bereits deine Stimme)
Write-Host ""
Write-Host "  Stimm-ID  (ElevenLabs Voice-ID)" -ForegroundColor Cyan
Write-Host "    Standard ist bereits hx3VHMzUAVVvishlV9u9 — leer lassen = so belassen." -ForegroundColor DarkGray
$vid = Read-Host "    JARVIS_VOICE_ID"
if ($vid.Trim().Length -gt 0) {
    setx JARVIS_VOICE_ID $vid.Trim() | Out-Null
    Write-Host "    [OK] Stimm-ID gesetzt." -ForegroundColor Green
} else {
    Write-Host "    (Standardstimme wird verwendet)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host "   Fertig. WICHTIG: JARVIS jetzt NEU STARTEN, damit die Keys" -ForegroundColor Green
Write-Host "   wirksam werden (Doppelklick auf 'JARVIS starten')." -ForegroundColor Green
Write-Host "   Danach ist alles automatisch verbunden — ohne Klicken." -ForegroundColor Green
Write-Host "  ============================================================" -ForegroundColor Green
Write-Host ""
Read-Host "  Enter zum Schliessen"
