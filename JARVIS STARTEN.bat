@echo off
REM ============================================================
REM  JARVIS AI OS - Start per Doppelklick (Windows)
REM  Startet den Server und oeffnet das Dashboard im Browser.
REM ============================================================
cd /d "%~dp0"

if not exist .env (
    echo WICHTIG: .env-Datei mit deinen API-Keys fehlt in diesem Ordner!
    echo JARVIS startet trotzdem, antwortet aber nur im Echo-Modus.
    echo.
)

echo   J.A.R.V.I.S. startet ... Dashboard oeffnet sich gleich im Browser.
start "" "http://127.0.0.1:8765"
python -m jarvis
pause
