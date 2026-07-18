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
    # 0) Ausdrücklicher Pfad per Umgebungsvariable (höchste Priorität)
    explicit = os.environ.get("JARVIS_CLAW_PATH")
    if explicit and Path(explicit).exists():
        return explicit
    # 1) PATH
    for name in CANDIDATES:
        found = shutil.which(name)
        if found:
            return found
    # 2) typische Windows-/Linux-Installationsorte
    bases = [os.environ.get("LOCALAPPDATA"), os.environ.get("USERPROFILE"),
             os.environ.get("HOME"), "/usr/local/bin", "/usr/bin"]
    rels = ("Programs/ClawCode/claw.exe", "Programs/ClawCode/claw",
            ".cargo/bin/claw.exe", ".cargo/bin/claw", "claw", "claw.exe",
            "Downloads/claw-code-main/rust/target/release/claw.exe",
            "Downloads/claw-code-main/rust/target/debug/claw.exe")
    for base in bases:
        if not base:
            continue
        for rel in rels:
            p = Path(base) / rel
            if p.exists():
                return str(p)
    return None


class CodeAgentPlugin(Plugin):
    name = "code"
    description = ("Claude Code / Claw als Werkzeug: echter Agent (Fable 5) falls "
                   "installiert, sonst Boss/Worker-Split (Sol Ultra implementiert, "
                   "Fable 5 reviewt)")
    dangerous = True                     # startet einen Agenten mit vollem Tool-Zugriff
    allowed_teams = ["Führung", "Softwareentwicklung", "KI-Entwicklung", "DevOps",
                     "Python-Team", "Rust-Team", "Web-Team", "Automatisierung",
                     "Qualitätsmanagement"]

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.binary = find_binary()

    def health(self) -> tuple[bool, str]:
        """Voll lauffähig nur mit echtem Agenten-Binary UND API-Key; sonst Gehirn-Fallback."""
        if not self.binary:
            return False, "kein claw/claude-Binary gefunden — Fallback auf JARVIS-Gehirn"
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return False, "kein API-Key gesetzt — Fallback auf JARVIS-Gehirn"
        return True, ""

    def status(self) -> dict:
        s = super().status()
        s["binary"] = self.binary or "keins gefunden (Fallback: JARVIS-Gehirn)"
        return s

    def _boss_worker_code(self, prompt: str) -> str:
        """Coding im Boss/Worker-Split: Sol Ultra (Worker) implementiert, Fable 5
        (Boss) reviewt und finalisiert. Ohne Sol-Worker (kein OpenRouter/OpenAI)
        genau EIN Fable-5-Durchgang — kein unnötiger Doppelaufruf."""
        from .identity import materialize
        emp = materialize("0")
        if not brain.worker_active():
            # Kein Sol-Worker -> ein einziger Durchgang über das Gehirn (Fable 5).
            return brain.answer(emp, prompt, role="worker")
        draft = brain.answer(
            emp,
            "Implementiere die folgende Coding-Aufgabe vollständig und konkret "
            "(Code + kurze Erklärung). Aufgabe:\n" + prompt,
            role="worker")
        final = brain.answer(
            emp,
            "Du bist der leitende Entwickler (Boss). Prüfe und verbessere die "
            "Umsetzung deines Workers: korrigiere Fehler, schärfe den Code und "
            "gib die FINALE, beste Fassung aus (Code + knappe Begründung der "
            "Änderungen). Aufgabe war:\n" + prompt +
            "\n\nWorker-Entwurf:\n" + draft,
            role="boss")
        return (f"[Code-Split — Worker {brain.WORKER_MODEL}, Boss "
                f"{brain.boss_model()}]\n{final}")

    def run(self, action: str = "prompt", prompt: str = "", model: str = "", **kwargs: object) -> object:
        if not prompt:
            raise ValueError("prompt= fehlt")
        model = model or brain.DEFAULT_MODEL

        # Kein echtes Agenten-Binary -> Boss/Worker-Split über das Gehirn
        # (Sol Ultra implementiert, Fable 5 reviewt). Braucht kein Binary und
        # folgt trotzdem Nates Modell-Aufteilung.
        if not self.binary:
            return "[Claude-Code-Binary nicht gefunden] " + self._boss_worker_code(prompt)
        # Binary da, aber kein Anthropic-Key -> ebenfalls Boss/Worker-Split.
        if not os.environ.get("ANTHROPIC_API_KEY"):
            return "[kein Anthropic-Key] " + self._boss_worker_code(prompt)

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
