@echo off
title JARVIS starten
cd /d "%~dp0"

echo.
echo   JARVIS wird gestartet - bitte warten...
echo   (Beim ersten Mal wird Python + Zubehoer eingerichtet, das dauert 1-2 Minuten.)
echo.

:: Alle Funktionen freischalten (PC-Steuerung + Shell/Code) - dauerhaft und fuer jetzt
setx JARVIS_ALLOW_PC 1 >nul 2>&1
setx JARVIS_ALLOW_DANGEROUS 1 >nul 2>&1
set "JARVIS_ALLOW_PC=1"
set "JARVIS_ALLOW_DANGEROUS=1"

:: JARVIS als eigene App starten (eigenes Fenster, verbindet sich autom. mit dem PC)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Jarvis.ps1" -Autopilot

echo.
echo   JARVIS wurde beendet. Fenster kann geschlossen werden.
pause
