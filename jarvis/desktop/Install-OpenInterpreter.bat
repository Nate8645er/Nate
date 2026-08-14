@echo off
title Open Interpreter Installer
cd /d "%~dp0"

echo.
echo ========================================
echo   Open Interpreter wird installiert (die Haende von JARVIS) ...
echo ========================================
echo.

rem --- API-Key pruefen (nur Hinweis, kein automatischer Abbruch) ---
if not "%ANTHROPIC_API_KEY%"=="" goto :key_ok

echo.
echo [HINWEIS] Es wurde kein ANTHROPIC_API_KEY gefunden.
echo Open Interpreter braucht diesen Schluessel, um mit Claude zu sprechen.
echo.
echo Key setzen mit:
echo   setx ANTHROPIC_API_KEY "sk-ant-..."
echo.
echo Danach ein NEUES Terminalfenster oeffnen, damit die Aenderung
echo wirksam wird, und dieses Skript erneut starten.
echo.
choice /c JN /m "Trotzdem mit der Installation fortfahren? [J/N]"
if errorlevel 2 goto :abort
goto :key_ok

:abort
echo.
echo Installation abgebrochen. Bitte API-Key setzen und dieses Skript
echo danach erneut starten.
echo.
pause
exit /b 1

:key_ok

rem --- Offizieller Open-Interpreter-Installer ---
echo.
echo Lade und fuehre den offiziellen Open-Interpreter-Installer aus ...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://www.openinterpreter.com/install.ps1 | iex"
if errorlevel 1 (
    echo.
    echo [WARNUNG] Der Installer hat einen Fehlercode zurueckgegeben.
    echo Bitte pruefe deine Internetverbindung. Falls "interpreter" danach
    echo trotzdem funktioniert, kann diese Warnung ignoriert werden.
    echo.
)

rem --- Minimale Konfiguration anlegen, falls noch keine vorhanden ist ---
set "OI_DIR=%USERPROFILE%\.openinterpreter"
set "OI_CONFIG=%OI_DIR%\config.toml"

if exist "%OI_CONFIG%" goto :config_done

echo.
echo Lege Standardkonfiguration an unter:
echo   "%OI_CONFIG%"
echo.

if not exist "%OI_DIR%" mkdir "%OI_DIR%" >nul 2>nul

(
    echo # Von JARVIS Desktop automatisch erzeugte Konfiguration.
    echo # Nutzt Claude von Anthropic ueber den ANTHROPIC_API_KEY.
    echo model_provider = "anthropic"
    echo model = "claude-opus-4-8"
    echo approval_policy = "on-request"
) > "%OI_CONFIG%"

:config_done

echo.
echo ========================================
echo  Fertig! So benutzt du die Haende von JARVIS:
echo.
echo  1. Oeffne ein NEUES Terminalfenster (wichtig, damit der
echo     ANTHROPIC_API_KEY sicher geladen wird).
echo  2. Tippe dort:  interpreter
echo  3. Open Interpreter fragt vor JEDEM Befehl um Bestaetigung,
echo     bevor er wirklich etwas auf diesem PC ausfuehrt.
echo  4. Beschreibe deine Aufgabe einfach auf Deutsch, zum Beispiel:
echo       "oeffne den Task-Manager"
echo.
echo  [WARNUNG] Open Interpreter fuehrt ECHTE Befehle auf diesem PC aus.
echo  Bestaetige nur Befehle, die du wirklich verstehst und auch
echo  wirklich ausfuehren moechtest!
echo ========================================
echo.
pause
