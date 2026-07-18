@echo off
setlocal
title OpenRouter-Key fuer JARVIS setzen
color 0A
cd /d "%~dp0"

echo.
echo   ============================================================
echo      OpenRouter-Key fuer JARVIS eintragen
echo   ============================================================
echo.
echo   Fuege deinen OpenRouter-Key ein (Rechtsklick = Einfuegen)
echo   und druecke Enter. Der Key beginnt mit  sk-or-
echo.
set "ORK="
set /p ORK="   OpenRouter-Key: "

if "%ORK%"=="" (
    echo.
    echo   Kein Key eingegeben - abgebrochen.
    pause
    exit /b 1
)

setx OPENROUTER_API_KEY "%ORK%" >nul
echo.
echo   [OK] OpenRouter-Key dauerhaft gespeichert.
echo.
echo   JARVIS verbindet sich beim naechsten Start automatisch damit.
echo   -> Jetzt JARVIS neu starten (JARVIS-Starten.cmd).
echo.
echo   Danach im Chat einfach eine Frage stellen - JARVIS nutzt dann
echo   automatisch die OpenRouter-Gratis-Modelle (kein Anthropic-Guthaben noetig).
echo.
pause
