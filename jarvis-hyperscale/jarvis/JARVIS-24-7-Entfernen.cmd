@echo off
title JARVIS 24/7 entfernen
cd /d "%~dp0"

echo.
echo   JARVIS 24/7 wird entfernt (startet dann nicht mehr automatisch)...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Jarvis-Service.ps1" -Uninstall

echo.
echo   Fertig.
pause
