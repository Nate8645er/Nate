#!/bin/bash
# Stellt sicher, dass Token Savior (token-savior-recall) im venv installiert ist.
# Idempotent: existiert das venv mit Binary bereits, ist das ein schneller No-op.
# Claude-Code-Remote-Container sind ephemer — dieses Skript macht die
# Installation in jeder frischen Session automatisch verfuegbar.
set -u
VENV="$HOME/.local/token-savior-venv"
BIN="$VENV/bin/token-savior"

[ -x "$BIN" ] && exit 0

if command -v uv > /dev/null 2>&1; then
  uv venv "$VENV" --python 3.11 > /dev/null 2>&1 || uv venv "$VENV" > /dev/null 2>&1
  uv pip install --python "$VENV/bin/python" "token-savior-recall[mcp,memory-vector]" > /dev/null 2>&1
else
  python3 -m venv "$VENV" > /dev/null 2>&1
  "$VENV/bin/pip" install --quiet "token-savior-recall[mcp,memory-vector]" > /dev/null 2>&1
fi

[ -x "$BIN" ]
