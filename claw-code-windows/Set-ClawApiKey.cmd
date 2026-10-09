@echo off
:: Claw Code - API-Key einrichten (Doppelklick genuegt)
:: Fragt den Anthropic API-Key ab, speichert ihn als Benutzer-Umgebungsvariable
:: und prueft die Installation mit 'claw doctor'.

title Claw Code - API-Key einrichten
echo.
echo  =====================================================
echo   Claw Code - API-Key einrichten
echo  =====================================================
echo.
echo  Deinen Key bekommst du hier (beginnt mit sk-ant-):
echo    https://console.anthropic.com  -^>  API Keys  -^>  Create Key
echo.
set /p CLAWKEY="  Key hier einfuegen (Rechtsklick = Einfuegen) und Enter: "

if "%CLAWKEY%"=="" (
    echo.
    echo  [X] Kein Key eingegeben - abgebrochen.
    pause
    exit /b 1
)

echo %CLAWKEY% | findstr /b "sk-ant-" >nul
if errorlevel 1 (
    echo.
    echo  [!] Hinweis: Der Key beginnt normalerweise mit "sk-ant-".
    echo      Er wird trotzdem gespeichert.
)

setx ANTHROPIC_API_KEY "%CLAWKEY%" >nul
set "ANTHROPIC_API_KEY=%CLAWKEY%"
set "CLAWKEY="

echo.
echo  [OK] ANTHROPIC_API_KEY wurde dauerhaft gespeichert.
echo.
echo  Pruefe die Installation mit 'claw doctor'...
echo  -----------------------------------------------------

where claw >nul 2>nul
if errorlevel 1 (
    if exist "%LOCALAPPDATA%\Programs\ClawCode\claw.exe" (
        "%LOCALAPPDATA%\Programs\ClawCode\claw.exe" doctor
    ) else (
        echo  [!] claw.exe nicht gefunden - bitte zuerst Install-ClawCode.ps1 ausfuehren.
    )
) else (
    claw doctor
)

echo  -----------------------------------------------------
echo.
echo  Fertig! Wenn oben unter "Auth" ein OK steht, ist alles aktiv.
echo  Offene Terminals muessen neu gestartet werden, damit sie den Key kennen.
echo.
pause
