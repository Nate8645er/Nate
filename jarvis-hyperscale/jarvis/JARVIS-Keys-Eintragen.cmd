@echo off
setlocal
title JARVIS - API-Keys eintragen
color 0A
cd /d "%~dp0"

echo.
echo   ============================================================
echo      JARVIS - API-Keys eintragen
echo   ============================================================
echo.
echo   Fuege bei jedem Punkt deinen Key ein (Rechtsklick = Einfuegen)
echo   und druecke Enter. Leer lassen = ueberspringen.
echo.
echo   ------------------------------------------------------------

echo.
echo   [1/3] Fable 5 / Claude  (Anthropic)
echo         Key von console.anthropic.com  (beginnt mit sk-ant-)
set "ANT="
set /p ANT="        Key hier einfuegen: "
if not "%ANT%"=="" (
    setx ANTHROPIC_API_KEY "%ANT%" >nul
    echo         [OK] Anthropic-Key gespeichert.
) else (
    echo         (uebersprungen)
)

echo.
echo   [2/3] Viele Modelle  (OpenRouter, 32 Modelle)
echo         Key von openrouter.ai/keys  (beginnt mit sk-or-)
set "ORK="
set /p ORK="        Key hier einfuegen: "
if not "%ORK%"=="" (
    setx OPENROUTER_API_KEY "%ORK%" >nul
    echo         [OK] OpenRouter-Key gespeichert.
) else (
    echo         (uebersprungen)
)

echo.
echo   [3/3] Echte Stimme  (ElevenLabs)
echo         Key von elevenlabs.io
set "ELK="
set /p ELK="        Key hier einfuegen: "
if not "%ELK%"=="" (
    setx ELEVENLABS_API_KEY "%ELK%" >nul
    echo         [OK] ElevenLabs-Key gespeichert.
) else (
    echo         (uebersprungen)
)

echo.
echo   ============================================================
echo    Fertig gespeichert. WICHTIG: JARVIS jetzt NEU STARTEN,
echo    damit die Keys wirken (Doppelklick auf "JARVIS starten").
echo    Danach ist alles automatisch verbunden.
echo   ============================================================
echo.
pause
