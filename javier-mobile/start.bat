@echo off
rem JAVIER MOBILE - Server starten (Windows)
cd /d %~dp0

where python >nul 2>nul
if errorlevel 1 (
    echo Python wurde nicht gefunden. Bitte von python.org installieren.
    pause
    exit /b 1
)

if not exist .venv (
    echo Erstelle virtuelle Umgebung und installiere Abhaengigkeiten...
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
)

if not exist .env (
    if exist .env.example copy .env.example .env >nul
    echo Hinweis: .env angelegt - API-Key wird gleich abgefragt.
)

echo.
echo Starte JAVIER... (Beenden mit Strg+C)
.venv\Scripts\python server.py
pause
