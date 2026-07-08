@echo off
chcp 65001 >nul
title Jarvis - KI-Assistent
cd /d "%~dp0"

echo ============================================
echo   Jarvis wird vorbereitet ...
echo ============================================
echo.

rem --- 0. Wurde die Datei direkt aus dem ZIP gestartet? ---
if not exist "requirements.txt" (
    echo [FEHLER] Die Jarvis-Dateien wurden hier nicht gefunden.
    echo.
    echo Wahrscheinlich wurde jarvis_starten.bat direkt aus der
    echo ZIP-Datei heraus gestartet. Das funktioniert nicht.
    echo.
    echo So geht es richtig:
    echo   1. Rechtsklick auf die ZIP-Datei - "Alle extrahieren ..."
    echo   2. Den entpackten Ordner oeffnen
    echo   3. Dort jarvis_starten.bat doppelklicken
    echo.
    pause
    exit /b 1
)

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

rem --- 2. Ollama pruefen (nur noetig fuer das lokale Gehirn) ---
set "HAS_OLLAMA=1"
where ollama >nul 2>nul
if errorlevel 1 (
    set "HAS_OLLAMA=0"
    echo [Hinweis] Ollama nicht gefunden - nur noetig, wenn provider "ollama" ist.
) else (
    echo [OK] Ollama gefunden.
)

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

rem --- 5. Lokales Sprachmodell pruefen, bei Bedarf laden (~2 GB, nur einmal) ---
if "%HAS_OLLAMA%"=="1" (
    ollama list 2>nul | findstr /i "llama3.2" >nul
    if errorlevel 1 (
        echo [...] Lade Sprachmodell llama3.2 herunter - das dauert einige Minuten ...
        ollama pull llama3.2
    )
    echo [OK] Lokales Sprachmodell bereit.
)

rem --- 6. Jarvis starten (Oberflaeche; bei Problemen Konsolen-Version) ---
echo.
echo ============================================
echo   Jarvis startet ...
echo ============================================
echo.
".venv\Scripts\python.exe" jarvis_gui.py
if errorlevel 1 (
    echo.
    echo [Hinweis] Oberflaeche konnte nicht starten - nutze Konsolen-Version.
    ".venv\Scripts\python.exe" main.py
)

echo.
pause
