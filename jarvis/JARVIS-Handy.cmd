@echo off
title JARVIS - Handy-Modus
cd /d "%~dp0"

echo.
echo   JARVIS wird im HANDY-MODUS gestartet...
echo   (Handy und PC muessen im SELBEN WLAN sein. Der PC muss anbleiben.)
echo.

:: Alle Funktionen freischalten (wie beim normalen Start)
setx JARVIS_ALLOW_PC 1 >nul 2>&1
setx JARVIS_ALLOW_DANGEROUS 1 >nul 2>&1
set "JARVIS_ALLOW_PC=1"
set "JARVIS_ALLOW_DANGEROUS=1"

:: Windows-Firewall fuer Port 8787 oeffnen (nur privates Netz). Best effort -
:: braucht evtl. Admin; schlaegt es fehl, laeuft JARVIS trotzdem (nur ggf. vom
:: Handy nicht erreichbar, dann einmal als Administrator ausfuehren).
netsh advfirewall firewall show rule name="JARVIS 8787" >nul 2>&1
if errorlevel 1 (
  netsh advfirewall firewall add rule name="JARVIS 8787" dir=in action=allow protocol=TCP localport=8787 profile=private >nul 2>&1
)

:: Handy-Modus: an 0.0.0.0 binden + eigene LAN-IP erlauben, dann App-Fenster oeffnen
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-Jarvis.ps1" -Autopilot -Lan

echo.
echo   JARVIS wurde beendet. Fenster kann geschlossen werden.
pause
