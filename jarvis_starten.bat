@echo off
chcp 65001 >nul
title Jarvis - KI-Assistent
cd /d "%~dp0"

echo ============================================
echo   Jarvis wird vorbereitet ...
echo ============================================
echo.

rem --- 1. Python finden (py oder python) ---
set "PYTHON=py"
where py >nul 2>nul
if errorlevel 1 (
    set "PYTHON=python"
    where python >nul 2>nul
    if errorlevel 1 (
        echo [FEHLER] Python wurde nicht gefunden.
        echo Bitte von https://www.python.org/downloads/ installieren
        echo und dabei "Add Python to PATH" anhaken.
        echo.
        pause
        exit /b 1
    )
)
echo [OK] Python gefunden.

rem --- 2. Ollama pruefen ---
where ollama >nul 2>nul
if errorlevel 1 (
    echo [FEHLER] Ollama wurde nicht gefunden.
    echo Bitte von https://ollama.com/download installieren.
    echo.
    pause
    exit /b 1
)
echo [OK] Ollama gefunden.

rem --- 3. Virtuelle Umgebung anlegen (nur beim ersten Start) ---
if not exist ".venv\Scripts\python.exe" (
    echo [...] Erstelle virtuelle Umgebung - einen Moment ...
    %PYTHON% -m venv .venv
    if errorlevel 1 (
        echo [FEHLER] Virtuelle Umgebung konnte nicht erstellt werden.
        pause
        exit /b 1
    )
)
echo [OK] Virtuelle Umgebung bereit.

rem --- 4. Abhaengigkeiten installieren/aktualisieren ---
echo [...] Pruefe Python-Pakete ...
".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [FEHLER] Pakete konnten nicht installiert werden.
    pause
    exit /b 1
)
echo [OK] Pakete installiert.

rem --- 5. Sprachmodell pruefen, bei Bedarf laden (~2 GB, nur einmal) ---
ollama list 2>nul | findstr /i "llama3.2" >nul
if errorlevel 1 (
    echo [...] Lade Sprachmodell llama3.2 herunter - das dauert einige Minuten ...
    ollama pull llama3.2
    if errorlevel 1 (
        echo [FEHLER] Modell konnte nicht geladen werden. Laeuft Ollama?
        pause
        exit /b 1
    )
)
echo [OK] Sprachmodell llama3.2 vorhanden.

rem --- 6. Jarvis starten ---
echo.
echo ============================================
echo   Jarvis startet ...
echo ============================================
echo.
".venv\Scripts\python.exe" main.py

echo.
pause
