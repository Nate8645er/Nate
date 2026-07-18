#!/bin/bash
# PreToolUse-Hook: Bash-Kommando-Rewriter (Token Savior) — dichtere Varianten
# wie `git status --porcelain=v2`, `pytest -q --tb=line` usw.
# Faellt lautlos auf No-op zurueck, solange das venv (noch) nicht installiert ist.
VENV="$HOME/.local/token-savior-venv"
HOOK=$(ls "$VENV"/lib/python*/site-packages/token_savior/hooks/bash_rewriter_hook.py 2>/dev/null | head -1)
[ -n "$HOOK" ] || exit 0
exec "$VENV/bin/python" "$HOOK"
