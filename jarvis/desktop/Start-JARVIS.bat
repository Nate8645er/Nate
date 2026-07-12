@echo off
title JARVIS Starter
cd /d "%~dp0"

echo.
echo ========================================
echo   JARVIS wird gestartet ...
echo ========================================
echo.

rem --- Python suchen (zuerst "python", dann den "py"-Launcher) ---
set "PY="
for /f "delims=" %%i in ('where python 2^>nul') do (
    if not defined PY set "PY=%%i"
)
if not defined PY (
    for /f "delims=" %%i in ('where py 2^>nul') do (
        if not defined PY set "PY=%%i"
    )
)
if not defined PY goto :no_python
goto :python_found

:no_python
echo.
echo [FEHLER] Es wurde keine Python-Installation gefunden.
echo.
echo Bitte installiere Python von https://www.python.org/downloads/
echo WICHTIG: Setze bei der Installation unbedingt den Haken bei
echo          "Add Python to PATH".
echo.
echo Starte diese Datei danach erneut.
echo.
pause
exit /b 1

:python_found

rem --- Pruefen, ob JARVIS.py im selben Ordner liegt ---
if not exist "%~dp0JARVIS.py" (
    echo.
    echo [FEHLER] Die Datei JARVIS.py wurde nicht gefunden in:
    echo   %~dp0
    echo.
    echo Bitte stelle sicher, dass Start-JARVIS.bat im selben Ordner
    echo wie JARVIS.py liegt, und starte diese Datei erneut.
    echo.
    pause
    exit /b 1
)

rem --- API-Key pruefen (nur Hinweis, kein Abbruch) ---
if "%ANTHROPIC_API_KEY%"=="" (
    echo.
    echo [HINWEIS] Es wurde kein ANTHROPIC_API_KEY gefunden.
    echo JARVIS startet trotzdem - im Dashboard erscheinen dann
    echo Anweisungen zur Einrichtung des API-Keys.
    echo.
    echo Key setzen mit:
    echo   setx ANTHROPIC_API_KEY "sk-ant-..."
    echo.
    echo Danach ein NEUES Terminalfenster oeffnen, damit die
    echo Aenderung wirksam wird.
    echo.
)

rem --- Autostart beim Hochfahren (optional) ---
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "STARTUP_BAT=%STARTUP_DIR%\JARVIS-Autostart.bat"

if exist "%STARTUP_BAT%" goto :autostart_done

echo.
choice /c JN /m "JARVIS beim Hochfahren automatisch starten? [J/N]"
if errorlevel 2 goto :autostart_done
if errorlevel 1 goto :autostart_enable
goto :autostart_done

:autostart_enable
if not exist "%STARTUP_DIR%" mkdir "%STARTUP_DIR%" >nul 2>nul
(
    echo @echo off
    echo cd /d "%~dp0"
    echo start "JARVIS" /min "%~dp0Start-JARVIS.bat"
) > "%STARTUP_BAT%"
echo.
echo Autostart wurde eingerichtet.
echo Zum Deaktivieren einfach diese Datei loeschen:
echo   %STARTUP_BAT%
echo.

:autostart_done

rem --- Abhaengigkeiten installieren ---
echo.
echo Installiere/aktualisiere benoetigte Python-Pakete ...
"%PY%" -m pip install --quiet --upgrade pip
"%PY%" -m pip install --quiet fastapi uvicorn anthropic

rem --- Hinweise vor dem Start ---
echo.
echo ========================================
echo  Der Browser oeffnet sich gleich automatisch.
echo  Klicke oben in der Konsole auf "Freihand" und sprich
echo  einfach los (z. B. "Jarvis, ...").
echo  Zum Beenden von JARVIS einfach dieses Fenster schliessen.
echo ========================================
echo.

rem --- JARVIS starten ---
"%PY%" "%~dp0JARVIS.py"

echo.
echo JARVIS wurde beendet.
pause
