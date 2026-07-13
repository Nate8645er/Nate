"""Claude-Code-Brücke für JARVIS — echter Agent-Binary mit Fable 5.

JARVIS kann eine vollständige Claude-Code-/Claw-Sitzung als Werkzeug nutzen:
findet automatisch ein installiertes Agenten-Binary (`claw`, `claude`,
`agent`) und ruft es im Arbeitsbereich mit dem konfigurierten Modell
(Standard: claude-fable-5) auf. Ist kein Binary vorhanden oder kein
API-Key gesetzt, fällt JARVIS auf das eigene Gehirn (brain.py) zurück und
sagt das ehrlich.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from . import brain
from .plugins import Plugin

CANDIDATES = ["claw", "claude", "agent"]


def find_binary() -> str | None:
    # 1) PATH
    for name in CANDIDATES:
        found = shutil.which(name)
        if found:
            return found
    # 2) typische Windows-Installationsorte
    for env in ("LOCALAPPDATA", "USERPROFILE"):
        base = os.environ.get(env)
        if not base:
            continue
        for rel in ("Programs/ClawCode/claw.exe", ".cargo/bin/claw.exe",
                    ".cargo/bin/claw", "Programs/ClawCode/claw"):
            p = Path(base) / rel
            if p.exists():
                return str(p)
    return None


class CodeAgentPlugin(Plugin):
    name = "code"
    description = "Claude Code / Claw als Werkzeug: Prompt an den echten Agenten (Fable 5)"
    dangerous = True                     # startet einen Agenten mit vollem Tool-Zugriff
    allowed_teams = ["Führung", "Softwareentwicklung", "KI-Entwicklung", "DevOps",
                     "Python-Team", "Rust-Team", "Web-Team", "Automatisierung",
                     "Qualitätsmanagement"]

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.binary = find_binary()

    def status(self) -> dict:
        s = super().status()
        s["binary"] = self.binary or "keins gefunden (Fallback: JARVIS-Gehirn)"
        return s

    def run(self, action: str = "prompt", prompt: str = "", model: str = "", **kwargs: object) -> object:
        if not prompt:
            raise ValueError("prompt= fehlt")
        model = model or brain.DEFAULT_MODEL

        # Kein Binary oder kein Key -> ehrlicher Fallback auf das JARVIS-Gehirn.
        if not self.binary or not os.environ.get("ANTHROPIC_API_KEY"):
            from .identity import materialize
            emp = materialize("0")
            note = ("[Claude-Code-Binary nicht gefunden] " if not self.binary
                    else "[kein API-Key] ")
            return note + brain.answer(emp, prompt)

        try:
            proc = subprocess.run(
                [self.binary, "--model", model, "prompt", prompt],
                cwd=self.workspace, capture_output=True, text=True, timeout=180,
                env={**os.environ, "CARGO_TERM_COLOR": "never"})
        except subprocess.TimeoutExpired:
            return "[Claude Code: Zeitüberschreitung nach 180s]"
        except Exception as e:
            return f"[Claude Code Fehler: {type(e).__name__}: {e}]"
        out = (proc.stdout or "") + (proc.stderr or "")
        return f"[claude-code via {Path(self.binary).name}, Modell {model}]\n{out.strip()[:4000]}"
