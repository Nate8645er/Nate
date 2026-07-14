"""Browser-Automatisierung für JARVIS — selbstständig im Web arbeiten.

JARVIS steuert einen echten Browser (Playwright): Seiten öffnen, Inhalt lesen,
Links auflisten, klicken, in Felder tippen, absenden, Screenshot. Damit kann
ein Mitarbeiter wirklich „im Browser arbeiten", nicht nur eine URL öffnen.

Technik: Playwright ist thread-gebunden, deshalb läuft der Browser in EINEM
eigenen Worker-Thread, der Befehle über eine Queue abarbeitet. Alle Aufrufe
gehen an denselben Browser/dieselbe Seite — der Zustand bleibt erhalten.

Sicherheit: gleiches Opt-in wie die PC-Steuerung (JARVIS_ALLOW_PC=1). Ist
Playwright nicht installiert, meldet das Werkzeug das ehrlich.

Sichtbar/headless: Auf Windows startet der Browser standardmäßig SICHTBAR
(du siehst JARVIS arbeiten); auf Servern/Linux headless. Override:
JARVIS_BROWSER_HEADLESS=1 (immer unsichtbar) bzw. =0 (immer sichtbar).
"""

from __future__ import annotations

import os
import queue
import re
import threading
from pathlib import Path
from typing import Any

from .plugins import Plugin


def _headless_default() -> bool:
    val = os.environ.get("JARVIS_BROWSER_HEADLESS")
    if val in ("0", "1"):
        return val == "1"
    return os.name != "nt"   # Windows: sichtbar; sonst headless


class _BrowserWorker(threading.Thread):
    def __init__(self, workspace: Path, headless: bool) -> None:
        super().__init__(daemon=True)
        self.workspace = workspace
        self.headless = headless
        self.cmds: queue.Queue = queue.Queue()
        self.ready = threading.Event()
        self.err: str | None = None

    def run(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:  # Playwright nicht installiert
            self.err = (f"Browser-Automatisierung nicht verfügbar ({type(e).__name__}). "
                        "Auf Windows: 'pip install playwright' und 'playwright install chromium'.")
            self.ready.set()
            return
        try:
            with sync_playwright() as pw:
                browser = None
                attempts: list[dict] = [
                    {"channel": "chrome"}, {"channel": "msedge"}, {},
                ]
                # Expliziter Chromium-Pfad (z. B. gebündelt auf Servern)
                exe = os.environ.get("PLAYWRIGHT_CHROMIUM_PATH")
                if not exe:
                    for cand in ("/opt/pw-browsers/chromium",
                                 "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"):
                        if os.path.exists(cand):
                            exe = cand
                            break
                if exe:
                    attempts.append({"executable_path": exe})
                for opts in attempts:
                    try:
                        browser = pw.chromium.launch(headless=self.headless, **opts)
                        break
                    except Exception:
                        continue
                if browser is None:
                    self.err = ("Kein Browser gefunden. Auf Windows Chrome/Edge installieren "
                                "oder 'playwright install chromium' ausführen.")
                    self.ready.set()
                    return
                page = browser.new_page()
                self.ready.set()
                while True:
                    cmd, resq = self.cmds.get()
                    if cmd is None:
                        break
                    try:
                        resq.put(("ok", self._do(page, cmd)))
                    except Exception as e:
                        resq.put(("err", f"{type(e).__name__}: {e}"))
                browser.close()
        except Exception as e:
            self.err = f"Browser-Fehler: {type(e).__name__}: {e}"
            self.ready.set()

    def _do(self, page: Any, cmd: dict) -> Any:
        action = cmd["action"]
        if action == "goto":
            url = cmd["url"]
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            return {"titel": page.title(), "url": page.url}
        if action == "read":
            text = page.inner_text("body")
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
            return text[:3000]
        if action == "links":
            out = []
            for a in page.query_selector_all("a")[:40]:
                t = (a.inner_text() or "").strip()
                href = a.get_attribute("href") or ""
                if t and href:
                    out.append(f"{t[:50]} -> {href[:90]}")
            return out or "Keine Links."
        if action == "click":
            page.click(cmd["ziel"], timeout=8000)
            return {"geklickt": cmd["ziel"], "url": page.url}
        if action == "type":
            page.fill(cmd["feld"], cmd["text"], timeout=8000)
            return {"getippt_in": cmd["feld"]}
        if action == "press":
            page.keyboard.press(cmd.get("taste", "Enter"))
            return {"taste": cmd.get("taste", "Enter"), "url": page.url}
        if action == "screenshot":
            path = self.workspace / "browser.png"
            page.screenshot(path=str(path))
            return {"gespeichert": str(path)}
        raise ValueError(f"Unbekannte Aktion: {action}")


class BrowserAutoPlugin(Plugin):
    name = "browser_auto"
    description = ("Browser selbst steuern: Seite öffnen, lesen, Links, klicken, "
                  "tippen, absenden (Playwright; Schalter JARVIS_ALLOW_PC)")
    dangerous = True
    allow_env = ["JARVIS_ALLOW_PC", "JARVIS_ALLOW_DANGEROUS"]
    allowed_teams = ["Führung", "Automatisierung", "Web-Team", "Recherche",
                     "KI-Entwicklung", "Qualitätsmanagement", "DevOps"]

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)
        self._worker: _BrowserWorker | None = None
        self._lock = threading.Lock()

    def _ensure(self) -> _BrowserWorker | str:
        with self._lock:
            if self._worker is None or not self._worker.is_alive():
                self._worker = _BrowserWorker(self.workspace, _headless_default())
                self._worker.start()
                self._worker.ready.wait(timeout=60)
            if self._worker.err:
                return self._worker.err
            return self._worker

    def _send(self, cmd: dict) -> Any:
        w = self._ensure()
        if isinstance(w, str):
            return w
        resq: queue.Queue = queue.Queue()
        w.cmds.put((cmd, resq))
        try:
            status, result = resq.get(timeout=60)
        except queue.Empty:
            return "Zeitüberschreitung im Browser."
        return result if status == "ok" else f"[Browser] {result}"

    def run(self, action: str = "read", **kwargs: Any) -> Any:
        if action == "goto":
            if not kwargs.get("url"):
                raise ValueError("url= fehlt")
            return self._send({"action": "goto", "url": kwargs["url"]})
        if action in ("read", "links", "screenshot"):
            return self._send({"action": action})
        if action == "click":
            if not kwargs.get("ziel"):
                raise ValueError("ziel= fehlt (Text oder CSS-Selektor)")
            return self._send({"action": "click", "ziel": kwargs["ziel"]})
        if action == "type":
            return self._send({"action": "type", "feld": kwargs.get("feld", ""),
                               "text": kwargs.get("text", "")})
        if action == "press":
            return self._send({"action": "press", "taste": kwargs.get("taste", "Enter")})
        raise ValueError(f"Unbekannte Aktion: {action} "
                         "(goto|read|links|click|type|press|screenshot)")


def register(manager: Any, workspace: Path) -> None:
    plugin = BrowserAutoPlugin(workspace)
    manager.plugins[plugin.name] = plugin
