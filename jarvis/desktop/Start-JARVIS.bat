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
echo Python ist nicht installiert - ich installiere es jetzt automatisch ...
echo.

set "INSTALL_OK="

where winget >nul 2>nul
if errorlevel 1 goto :try_ps_installer

echo Installiere Python ueber winget ...
winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
if errorlevel 1 goto :try_ps_installer
set "INSTALL_OK=1"
goto :install_done

:try_ps_installer
echo Installiere Python ueber den offiziellen Installer von python.org ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile \"$env:TEMP\python-setup.exe\""
if errorlevel 1 goto :install_failed

"%TEMP%\python-setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
if errorlevel 1 goto :install_failed

del /q "%TEMP%\python-setup.exe" >nul 2>nul
set "INSTALL_OK=1"
goto :install_done

:install_failed
del /q "%TEMP%\python-setup.exe" >nul 2>nul
goto :install_done

:install_done
if defined INSTALL_OK goto :install_success

echo.
echo [FEHLER] Die automatische Installation von Python ist fehlgeschlagen.
echo.
echo Bitte installiere Python manuell von https://www.python.org/downloads/
echo WICHTIG: Setze bei der Installation unbedingt den Haken bei
echo          "Add Python to PATH".
echo.
echo Starte diese Datei danach erneut.
echo.
pause
exit /b 1

:install_success
echo.
echo Installation abgeschlossen.
echo Bitte dieses Fenster schliessen und Start-JARVIS.bat ERNEUT
echo doppelklicken - dann geht es automatisch weiter.
echo.
pause
exit /b 0

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

rem --- Optional: Claude Code Plugin "fable-baton" einrichten ---
echo.
where claude >nul 2>nul
if errorlevel 1 goto :claude_not_found

echo Claude Code gefunden - richte fable-baton ein ...
claude plugin marketplace add realgarit/fable-baton >nul 2>nul
claude plugin install fable-baton@fable-baton >nul 2>nul
echo fable-baton ist eingerichtet (aktiv ab der naechsten Claude-Code-Session).
goto :fable_baton_done

:claude_not_found
echo Claude Code wurde nicht gefunden - das ist optional.
echo Falls gewuenscht, richtet Start-JARVIS.bat fable-baton automatisch ein,
echo sobald Claude Code installiert ist. Download: https://claude.com/claude-code

:fable_baton_done

rem --- Optional: Open Interpreter (die Haende) einrichten ---
echo.
where interpreter >nul 2>nul
if errorlevel 1 goto :oi_not_found

echo Open Interpreter ist bereits installiert.
goto :oi_done

:oi_not_found
choice /c JN /m "Open Interpreter jetzt installieren (fuehrt Befehle auf diesem PC aus)? [J/N]"
if errorlevel 2 goto :oi_skip
if errorlevel 1 goto :oi_install
goto :oi_done

:oi_install
if exist "%~dp0Install-OpenInterpreter.bat" goto :oi_install_script
echo.
echo Installiere Open Interpreter ueber den offiziellen Installer ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://www.openinterpreter.com/install.ps1 | iex"
if errorlevel 1 (
    echo.
    echo [HINWEIS] Die Installation von Open Interpreter ist fehlgeschlagen.
    echo Du kannst es spaeter jederzeit per Install-OpenInterpreter.bat nachholen.
)
goto :oi_done

:oi_install_script
call "%~dp0Install-OpenInterpreter.bat"
goto :oi_done

:oi_skip
echo Uebersprungen - spaeter jederzeit per Install-OpenInterpreter.bat nachholbar.

:oi_done

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
