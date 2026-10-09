@echo off
title JARVIS auf NUR OpenRouter (gratis, ohne Fable 5)
color 0A
cd /d "%~dp0"

echo.
echo   ============================================================
echo      JARVIS: Fable 5 aus - nur OpenRouter-Gratis-Modelle
echo   ============================================================
echo.
echo   Damit ueberspringt JARVIS Fable 5 komplett und nutzt NUR die
echo   kostenlosen OpenRouter-Modelle. Du brauchst dann KEINEN
echo   Anthropic-Key und KEIN Guthaben - nur den OpenRouter-Key.
echo.

setx JARVIS_BRAIN openrouter >nul
echo   [OK] Umgestellt auf: nur OpenRouter.
echo.
echo   Voraussetzung: OpenRouter-Key ist gesetzt (OpenRouter-Key-Setzen.cmd).
echo.
echo   -> Jetzt JARVIS neu starten (JARVIS-Starten.cmd), dann eine Frage
echo      im Chat stellen. Es kommt eine echte Antwort ueber ein Gratis-Modell.
echo.
echo   (Zurueck zu Fable 5 spaeter:  setx JARVIS_BRAIN auto  )
echo.
pause
