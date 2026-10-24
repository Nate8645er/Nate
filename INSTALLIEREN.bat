@echo off
REM ============================================================
REM  JARVIS AI OS - Installation per Doppelklick (Windows)
REM  Installiert alles und richtet den Autostart ein.
REM ============================================================
cd /d "%~dp0"
echo.
echo   J.A.R.V.I.S. wird installiert ...
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo FEHLER: Python wurde nicht gefunden.
    echo Bitte zuerst Python 3.11+ von https://www.python.org/downloads/ installieren
    echo und dabei das Haekchen "Add Python to PATH" setzen.
    pause
    exit /b 1
)

echo [1/3] Installiere JARVIS ...
python -m pip install -e . || (echo Installation fehlgeschlagen & pause & exit /b 1)

echo [2/3] Installiere Sprach-Stack (Mikrofon, Wake Word) ...
python -m pip install -e ".[voice]" || echo Hinweis: Sprach-Stack optional - Browser-Sprache geht trotzdem.

echo [3/3] Richte Autostart ein ...
powershell -ExecutionPolicy Bypass -File scripts\install-autostart-windows.ps1

if not exist .env (
    echo.
    echo WICHTIG: Lege noch deine .env-Datei ^(mit den API-Keys^) in diesen Ordner!
)

echo.
echo ============================================================
echo   Fertig! JARVIS startet ab jetzt automatisch mit dem PC.
echo   Sofort loslegen: Doppelklick auf "JARVIS STARTEN.bat"
echo ============================================================
pause
