@echo off
title JARVIS mit Claw Code verbinden
cd /d "%~dp0"

echo.
echo   JARVIS mit Claw Code (claw.exe) verbinden
echo   =========================================
echo.
echo   JARVIS findet claw.exe normalerweise automatisch, wenn es unter
echo   %%LOCALAPPDATA%%\Programs\ClawCode\claw.exe installiert ist
echo   (ueber den Claw-Code-Windows-Installer).
echo.
echo   Falls deine claw.exe woanders liegt, ziehe sie hier ins Fenster
echo   (oder tippe den vollen Pfad) und druecke Enter:
echo.
set /p CLAWPATH="  Pfad zu claw.exe (leer = automatisch suchen): "

if "%CLAWPATH%"=="" (
    echo.
    echo   Keine Angabe - JARVIS sucht claw.exe automatisch. Fertig.
    pause
    exit /b 0
)

set "CLAWPATH=%CLAWPATH:"=%"
if not exist "%CLAWPATH%" (
    echo.
    echo   [X] Datei nicht gefunden: %CLAWPATH%
    pause
    exit /b 1
)

setx JARVIS_CLAW_PATH "%CLAWPATH%" >nul
echo.
echo   [OK] Verbunden. JARVIS nutzt jetzt: %CLAWPATH%
echo   Bitte JARVIS neu starten (JARVIS-Starten.cmd).
echo.
echo   Danach im Chat/per Sprache z. B.:  "claw code schreibe eine Python Funktion"
pause
