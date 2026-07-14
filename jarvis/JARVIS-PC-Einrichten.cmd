@echo off
title JARVIS fuer diesen PC einrichten
cd /d "%~dp0"

echo.
echo   ============================================================
echo     JARVIS fuer DIESEN PC einrichten (einmalig)
echo   ============================================================
echo.
echo   Das hier richtet alles ein, damit JARVIS deinen PC steuern kann:
echo     - Python + alle Bausteine installieren
echo     - PC-Steuerung freischalten (Programme, Maus, Tastatur, Bildschirm)
echo     - Browser-Steuerung einrichten
echo     - ein Desktop-Symbol "JARVIS starten" anlegen
echo.
echo   Danach startet JARVIS und das Dashboard oeffnet sich im Browser.
echo.
echo   HINWEIS: Damit darf JARVIS deinen Rechner bedienen wie du selbst.
echo   Nur auf deinem EIGENEN, vertrauenswuerdigen PC ausfuehren.
echo.
pause

echo.
echo   [1/2] PC-Steuerung dauerhaft freischalten...
setx JARVIS_ALLOW_PC 1 >nul 2>&1
setx JARVIS_ALLOW_DANGEROUS 1 >nul 2>&1
set "JARVIS_ALLOW_PC=1"
set "JARVIS_ALLOW_DANGEROUS=1"
echo         OK - PC-Steuerung ist freigeschaltet.

echo.
echo   [2/2] Installieren + einrichten (beim ersten Mal 1-3 Minuten)...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Jarvis.ps1" -Setup -Autopilot

echo.
echo   JARVIS wurde beendet. Ab jetzt reicht ein Doppelklick auf das
echo   Desktop-Symbol "JARVIS starten" (oder auf JARVIS-Starten.cmd).
echo.
pause
