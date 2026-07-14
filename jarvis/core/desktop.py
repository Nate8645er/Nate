"""PC-Steuerung für JARVIS — Programme, Maus, Tastatur, Bildschirm.

Dies ist die mächtigste (und riskanteste) Fähigkeit: ein aktiver Mitarbeiter
kann damit deinen ganzen Rechner bedienen, wie du selbst. Deshalb steckt sie
hinter einem EIGENEN, standardmäßig ausgeschalteten Schalter:

    JARVIS_ALLOW_PC=1   (bewusst setzen, nur auf deinem eigenen PC)

Getrennt von JARVIS_ALLOW_DANGEROUS (Shell/Code), damit du „PC bedienen"
freischalten kannst, ohne gleich beliebige Shell-Befehle zu erlauben.

Technik: Maus/Tastatur/Screenshot via pyautogui (auf Windows vorhanden bzw.
per pip installiert). Fehlt die Bibliothek oder läuft kein Desktop (z. B. auf
einem Server), meldet das Werkzeug das ehrlich, statt abzustürzen.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from .plugins import Plugin


def _pyautogui():
    """Lazy-Import: pyautogui braucht einen echten Desktop (nicht headless)."""
    import pyautogui
    pyautogui.FAILSAFE = True   # Maus in die Ecke = Not-Aus
    return pyautogui


class PCControlPlugin(Plugin):
    name = "pc"
    description = ("PC steuern: Programme öffnen/schließen, Maus, Tastatur, "
                  "Screenshot (eigener Schalter JARVIS_ALLOW_PC)")
    dangerous = True
    allow_env = ["JARVIS_ALLOW_PC", "JARVIS_ALLOW_DANGEROUS"]
    allowed_teams = ["Führung", "Automatisierung", "DevOps", "Qualitätsmanagement",
                     "Softwareentwicklung", "KI-Entwicklung"]

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)

    # -- Programme -----------------------------------------------------------
    def _open(self, target: str) -> str:
        if not target:
            raise ValueError("program= fehlt (z. B. notepad, calc, https://…, C:\\pfad)")
        if os.name == "nt":
            try:
                os.startfile(target)  # type: ignore[attr-defined]
                return f"geöffnet: {target}"
            except Exception:
                subprocess.Popen(["cmd", "/c", "start", "", target], shell=False)
                return f"gestartet: {target}"
        # macOS/Linux
        opener = "open" if os.uname().sysname == "Darwin" else "xdg-open"
        try:
            subprocess.Popen([opener, target])
            return f"geöffnet: {target}"
        except FileNotFoundError:
            try:
                subprocess.Popen([target], shell=False)
                return f"gestartet: {target}"
            except Exception as e:
                return f"konnte nicht öffnen: {target} ({type(e).__name__})"

    def _close(self, name: str) -> str:
        if not name:
            raise ValueError("name= fehlt (Prozess-/Programmname, z. B. notepad.exe)")
        if os.name == "nt":
            r = subprocess.run(["taskkill", "/IM", name, "/F"],
                               capture_output=True, text=True)
            return (r.stdout or r.stderr).strip() or f"beendet: {name}"
        import psutil
        killed = 0
        for p in psutil.process_iter(["name"]):
            if p.info["name"] and name.lower() in p.info["name"].lower():
                try:
                    p.kill(); killed += 1
                except Exception:
                    pass
        return f"{killed} Prozess(e) beendet: {name}"

    # -- Maus / Tastatur / Bildschirm ---------------------------------------
    def run(self, action: str = "screenshot", **kwargs: Any) -> Any:
        if action == "open":
            return self._open(kwargs.get("program", ""))
        if action == "close":
            return self._close(kwargs.get("name", ""))
        if action == "apps":
            import psutil
            names = sorted({p.info["name"] for p in psutil.process_iter(["name"])
                            if p.info["name"]})
            return names[:80]

        # Ab hier braucht es einen echten Desktop.
        try:
            gui = _pyautogui()
        except Exception as e:
            return (f"PC-Eingabe nicht verfügbar ({type(e).__name__}). "
                    "pyautogui installieren und an einem echten Desktop ausführen "
                    "(nicht headless/Server).")

        if action == "move":
            gui.moveTo(int(kwargs.get("x", 0)), int(kwargs.get("y", 0)),
                       duration=0.2)
            return f"Maus bei ({kwargs.get('x')}, {kwargs.get('y')})"
        if action == "click":
            x, y = kwargs.get("x"), kwargs.get("y")
            button = kwargs.get("button", "left")
            if x is not None and y is not None:
                gui.click(int(x), int(y), button=button)
            else:
                gui.click(button=button)
            return f"Klick ({button})"
        if action == "type":
            text = kwargs.get("text", "")
            gui.typewrite(text, interval=0.02)
            return f"getippt: {len(text)} Zeichen"
        if action == "key":
            keys = [k for k in kwargs.get("keys", "").replace("+", " ").split() if k]
            if not keys:
                raise ValueError("keys= fehlt (z. B. keys=ctrl+s oder keys=enter)")
            gui.hotkey(*keys)
            return f"Tasten: {'+'.join(keys)}"
        if action == "screenshot":
            path = self.workspace / "screenshot.png"
            img = gui.screenshot()
            img.save(path)
            return {"gespeichert": str(path), "groesse": list(img.size)}

        raise ValueError(f"Unbekannte Aktion: {action} "
                         "(open|close|apps|move|click|type|key|screenshot)")


def register(manager: Any, workspace: Path) -> None:
    plugin = PCControlPlugin(workspace)
    manager.plugins[plugin.name] = plugin
