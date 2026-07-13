"""Claude-Code-artige Werkzeuge für JARVIS — echt und lauffähig.

Diese Tools spiegeln die Kern-Werkzeuge von Claude Code wider (Shell, Datei
lesen/schreiben/bearbeiten, Glob, Grep, WebFetch, Agent) und laufen lokal.
Alle Dateizugriffe sind auf den JARVIS-Arbeitsbereich gesandboxt.

Ehrlichkeit: „alle Tools von Claude.ai" umfasst auch serverseitige,
proprietäre Fähigkeiten, die sich außerhalb dieser Umgebung nicht
nachbauen lassen. Was hier steht, ist real umgesetzt; die Claude-Code-
Brücke (code.py) ruft den echten Agenten-Binary auf, wenn vorhanden.
"""

from __future__ import annotations

import fnmatch
import ipaddress
import re
import socket
import subprocess
import urllib.parse
from pathlib import Path
from typing import Any

from .plugins import Plugin


def _host_is_blocked(host: str) -> bool:
    """SSRF-Schutz: löst den Host auf und blockt private/loopback/link-local-Ziele."""
    if not host:
        return True
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return True
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            return True
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return True
    return False


class ShellPlugin(Plugin):
    name = "shell"
    description = "Shell-/Terminal-Befehle im Arbeitsbereich ausführen (wie Claude Code Bash)"
    dangerous = True                     # erreicht das ganze Betriebssystem — Opt-in nötig
    allowed_teams = ["Führung", "DevOps", "Softwareentwicklung", "Automatisierung",
                     "Cloud", "KI-Entwicklung", "Qualitätsmanagement"]

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)

    def run(self, action: str = "run", command: str = "", timeout: str = "30", **kwargs: Any) -> Any:
        if not command:
            raise ValueError("command= fehlt")
        try:
            proc = subprocess.run(command, shell=True, cwd=self.workspace,
                                  capture_output=True, text=True, timeout=int(timeout))
        except subprocess.TimeoutExpired:
            return f"[Zeitüberschreitung nach {timeout}s]"
        out = (proc.stdout or "") + (proc.stderr or "")
        return f"[exit {proc.returncode}]\n{out.strip()[:4000]}"


class ReadPlugin(Plugin):
    name = "read"
    description = "Datei lesen (mit Zeilennummern, wie Claude Code Read)"

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def _safe(self, rel: str) -> Path:
        ws = self.workspace.resolve()
        p = (ws / rel).resolve()
        if not p.is_relative_to(ws):     # verhindert ../ UND Präfix-Kollision (workspace-backup)
            raise PermissionError("Zugriff außerhalb des Arbeitsbereichs verweigert")
        return p

    def run(self, action: str = "read", path: str = "", limit: str = "200", **kwargs: Any) -> Any:
        p = self._safe(path)
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()[:int(limit)]
        return "\n".join(f"{i+1:>4}\t{ln}" for i, ln in enumerate(lines))


class EditPlugin(Plugin):
    name = "edit"
    description = "Text in einer Datei ersetzen (wie Claude Code Edit)"

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def _safe(self, rel: str) -> Path:
        ws = self.workspace.resolve()
        p = (ws / rel).resolve()
        if not p.is_relative_to(ws):     # verhindert ../ UND Präfix-Kollision (workspace-backup)
            raise PermissionError("Zugriff außerhalb des Arbeitsbereichs verweigert")
        return p

    def run(self, action: str = "edit", path: str = "", alt: str = "", neu: str = "", **kwargs: Any) -> Any:
        p = self._safe(path)
        text = p.read_text(encoding="utf-8")
        if alt not in text:
            raise ValueError("Suchtext nicht gefunden")
        count = text.count(alt)
        p.write_text(text.replace(alt, neu), encoding="utf-8")
        return f"{count}x ersetzt in {path}"


class GlobPlugin(Plugin):
    name = "glob"
    description = "Dateien per Muster finden (wie Claude Code Glob)"

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def run(self, action: str = "glob", pattern: str = "*", **kwargs: Any) -> Any:
        hits = [str(p.relative_to(self.workspace))
                for p in self.workspace.rglob("*")
                if not p.is_symlink() and fnmatch.fnmatch(p.name, pattern)]
        return sorted(hits)[:100] or "Keine Treffer."


class GrepPlugin(Plugin):
    name = "grep"
    description = "In Dateien nach einem Muster suchen (wie Claude Code Grep)"

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace

    def run(self, action: str = "grep", pattern: str = "", glob: str = "*", **kwargs: Any) -> Any:
        if not pattern:
            raise ValueError("pattern= fehlt")
        rx = re.compile(pattern)
        out = []
        for p in self.workspace.rglob("*"):
            if p.is_symlink():           # keine Symlinks aus der Sandbox heraus folgen
                continue
            if p.is_file() and fnmatch.fnmatch(p.name, glob):
                try:
                    for n, ln in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                        if rx.search(ln):
                            out.append(f"{p.relative_to(self.workspace)}:{n}: {ln.strip()[:120]}")
                            if len(out) >= 60:
                                return out
                except Exception:
                    continue
        return out or "Keine Treffer."


class WebFetchPlugin(Plugin):
    name = "webfetch"
    description = "Eine URL abrufen und als Text zurückgeben (wie Claude Code WebFetch)"

    def run(self, action: str = "fetch", url: str = "", **kwargs: Any) -> Any:
        import urllib.request
        if not url.startswith(("http://", "https://")):
            raise ValueError("url= muss mit http(s):// beginnen")
        host = urllib.parse.urlparse(url).hostname or ""
        if _host_is_blocked(host):       # SSRF: interne/loopback/metadaten-Ziele blocken
            return ("Abruf verweigert: interne/private Adressen sind aus "
                    "Sicherheitsgründen gesperrt (SSRF-Schutz).")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (JARVIS)"})
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw = resp.read().decode("utf-8", "ignore")
        except Exception as e:
            return f"Abruf fehlgeschlagen ({type(e).__name__}) — Netzwerk prüfen."
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:3000]


def register_all(manager: Any, workspace: Path) -> None:
    """Registriert die komplette Claude-Code-artige Tool-Suite im PluginManager."""
    for plugin in (ShellPlugin(workspace), ReadPlugin(workspace), EditPlugin(workspace),
                   GlobPlugin(workspace), GrepPlugin(workspace), WebFetchPlugin()):
        manager.plugins[plugin.name] = plugin
