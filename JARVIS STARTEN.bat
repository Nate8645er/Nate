@echo off
REM ============================================================
REM  JARVIS AI OS - Start per Doppelklick (Windows)
REM  Prueft alles, startet den Server und oeffnet das Dashboard
REM  erst, wenn der Server wirklich bereit ist.
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"
title JARVIS Start
echo.
echo   J.A.R.V.I.S. wird gestartet ...
echo.

REM --- 1) Python vorhanden? ---
where python >nul 2>nul
if errorlevel 1 (
    echo FEHLER: Python wurde nicht gefunden.
    echo.
    echo Loesung: Python 3.11+ installieren: https://www.python.org/downloads/
    echo WICHTIG: Beim Installieren "Add Python to PATH" ankreuzen,
    echo danach INSTALLIEREN.bat erneut ausfuehren.
    echo.
    pause
    exit /b 1
)

REM --- 2) JARVIS installiert? ---
python -c "import jarvis" >nul 2>nul
if errorlevel 1 (
    echo JARVIS ist noch nicht installiert.
    echo Starte jetzt automatisch die Installation ...
    echo.
    python -m pip install -e . || (
        echo.
        echo FEHLER bei der Installation - Text oben abfotografieren und Claude schicken.
        pause
        exit /b 1
    )
)

REM --- 3) .env da? ---
if not exist .env (
    echo HINWEIS: .env-Datei fehlt in diesem Ordner!
    echo JARVIS startet trotzdem, antwortet aber nur im Echo-Modus.
    echo.
)

REM --- 4) Server in eigenem Fenster starten (bleibt offen, zeigt Fehler) ---
start "JARVIS Server - dieses Fenster offen lassen" cmd /k python -m jarvis

REM --- 5) Warten bis der Server antwortet, dann Browser oeffnen ---
echo Warte auf den Server ...
set tries=0
:wait
set /a tries+=1
powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8765/api/status -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>nul
if not errorlevel 1 goto up
if !tries! geq 30 (
    echo.
    echo Der Server antwortet nicht. Schau in das Fenster "JARVIS Server" -
    echo dort steht die Fehlermeldung. Abfotografieren und Claude schicken.
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul
goto wait

:up
echo Server laeuft! Oeffne Dashboard ...
start "" "http://127.0.0.1:8765"
echo.
echo   Fertig - JARVIS laeuft. Dieses Fenster darfst du schliessen.
echo   (Das Fenster "JARVIS Server" muss offen bleiben.)
timeout /t 5 >nul
exit /b 0
