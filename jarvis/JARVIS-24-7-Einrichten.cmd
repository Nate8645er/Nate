@echo off
title JARVIS 24/7 einrichten
cd /d "%~dp0"

echo.
echo   JARVIS 24/7 wird eingerichtet.
echo   Danach startet JARVIS bei jeder Windows-Anmeldung automatisch im
echo   Hintergrund - ganz ohne Doppelklick, ohne PowerShell.
echo.

:: Alle Funktionen dauerhaft freischalten (PC-Steuerung + Shell/Code)
setx JARVIS_ALLOW_PC 1 >nul 2>&1
setx JARVIS_ALLOW_DANGEROUS 1 >nul 2>&1

:: Geplante Aufgabe registrieren (Autostart bei Anmeldung, Neustart bei Absturz)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Jarvis-Service.ps1"

echo.
echo   Fertig. Dashboard jederzeit unter:  http://127.0.0.1:8787
echo   (Zum Abschalten: JARVIS-24-7-Entfernen.cmd doppelklicken.)
pause
