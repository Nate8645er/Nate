@echo off
REM ai-team launcher für Windows cmd.exe / PowerShell (wenn bin\ auf PATH liegt)
where node >nul 2>nul
if errorlevel 1 (
  echo ai-team: Node.js wird benoetigt ^(node nicht auf PATH gefunden^). Installiere Node ^>=18.
  exit /b 1
)
node "%~dp0..\src\ai-team.mjs" %*
