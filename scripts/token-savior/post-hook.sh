#!/bin/bash
# PostToolUse-Hook: Bash-Output-Kompaktierung + Capture-Sandbox (Token Savior).
# Faellt lautlos auf No-op zurueck, solange das venv (noch) nicht installiert ist.
VENV="$HOME/.local/token-savior-venv"
HOOK=$(ls "$VENV"/lib/python*/site-packages/token_savior/hooks/tool_capture_hook.py 2>/dev/null | head -1)
[ -n "$HOOK" ] || exit 0
exec "$VENV/bin/python" "$HOOK"
