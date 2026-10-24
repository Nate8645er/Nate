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


def _split(selectors: str) -> list[str]:
    """Komma-getrennte CSS-Selektoren in Einzel-Selektoren zerlegen."""
    return [s.strip() for s in selectors.split(",") if s.strip()]


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
                # Eigenes, DAUERHAFTES JARVIS-Profil: Cookies/Sessions überleben
                # Neustarts -> einmal eingeloggt, bleibt eingeloggt ("überall
                # angemeldet"). Getrennt vom normalen Chrome-Profil, damit es
                # keine Konflikte gibt.
                profile = self.workspace / "browser-profile"
                profile.mkdir(parents=True, exist_ok=True)
                context = None
                attempts: list[dict] = [
                    {"channel": "chrome"}, {"channel": "msedge"}, {},
                ]
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
                        context = pw.chromium.launch_persistent_context(
                            str(profile), headless=self.headless,
                            accept_downloads=True, **opts)
                        break
                    except Exception:
                        continue
                if context is None:
                    self.err = ("Kein Browser gefunden. Auf Windows Chrome/Edge installieren "
                                "oder 'playwright install chromium' ausführen.")
                    self.ready.set()
                    return
                page = context.pages[0] if context.pages else context.new_page()
                self.ready.set()
                while True:
                    cmd, resq = self.cmds.get()
                    if cmd is None:
                        break
                    try:
                        resq.put(("ok", self._do(page, cmd)))
                    except Exception as e:
                        resq.put(("err", f"{type(e).__name__}: {e}"))
                context.close()
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
        if action == "login":
            return self._login(page, cmd)
        raise ValueError(f"Unbekannte Aktion: {action}")

    def _login(self, page: Any, cmd: dict) -> Any:
        """Loggt sich mit hinterlegten Zugangsdaten ein. Ehrlich bei 2FA/Captcha:
        JARVIS füllt Benutzer + Passwort und sendet ab; erscheint danach 2FA
        oder ein Captcha, wird das gemeldet (du erledigst diesen Schritt im
        sichtbaren Fenster). Cookies bleiben im JARVIS-Profil -> danach dauerhaft
        angemeldet."""
        plattform = cmd.get("plattform", "?")
        login_url = cmd["login_url"]
        if not login_url.startswith(("http://", "https://")):
            login_url = "https://" + login_url
        page.goto(login_url, timeout=30000, wait_until="domcontentloaded")

        # 1) Benutzername tippen
        try:
            page.fill(cmd["user_sel"], cmd["user"], timeout=8000)
        except Exception:
            return {"plattform": plattform, "status": "kein_loginfeld",
                    "hinweis": ("Benutzerfeld nicht gefunden — evtl. schon eingeloggt, "
                                "oder die Login-Seite/Selektoren stimmen nicht.")}

        # 2) Passwortfeld füllen. Ist es (noch) nicht sichtbar (2-Schritt-Login
        #    wie Google), erst 'Weiter' klicken, dann Passwort.
        def _fill_pass() -> bool:
            try:
                page.fill(cmd["pass_sel"], cmd["pass"], timeout=4000)
                return True
            except Exception:
                return False

        if not _fill_pass():
            for sel in _split(cmd["submit_sel"]):
                try:
                    page.click(sel, timeout=3000)
                    break
                except Exception:
                    continue
            page.wait_for_timeout(1500)
            _fill_pass()

        # 3) Absenden
        clicked = False
        for sel in _split(cmd["submit_sel"]):
            try:
                page.click(sel, timeout=3000)
                clicked = True
                break
            except Exception:
                continue
        if not clicked:
            try:
                page.keyboard.press("Enter")
            except Exception:
                pass
        page.wait_for_timeout(2500)

        # 4) Ergebnis ehrlich bewerten
        path = self.workspace / "login.png"
        try:
            page.screenshot(path=str(path))
        except Exception:
            pass
        body = ""
        try:
            body = page.inner_text("body")[:4000].lower()
        except Exception:
            pass
        needs_2fa = any(k in body for k in (
            "verifizierung", "verification code", "bestätigungscode", "2-step",
            "zwei-faktor", "two-factor", "authenticator", "einmalcode", "one-time",
            "sms", "code gesendet", "code sent"))
        captcha = "captcha" in body or "recaptcha" in body or "roboter" in body or "not a robot" in body
        wrong = any(k in body for k in (
            "falsches passwort", "incorrect password", "wrong password",
            "passwort ist falsch", "couldn't find your", "konto nicht gefunden"))
        if wrong:
            status = "falsche_daten"
        elif captcha:
            status = "captcha"
        elif needs_2fa:
            status = "2fa_noetig"
        else:
            status = "vermutlich_ok"
        return {"plattform": plattform, "status": status, "url": page.url,
                "screenshot": str(path),
                "hinweis": {
                    "falsche_daten": "Benutzername/Passwort scheinen falsch.",
                    "captcha": "Captcha aufgetaucht — bitte im sichtbaren Fenster lösen.",
                    "2fa_noetig": "2FA/Code nötig — bitte im sichtbaren Fenster eingeben; danach bleibt JARVIS angemeldet.",
                    "vermutlich_ok": "Login abgeschickt. Session im JARVIS-Profil gespeichert — du bleibst angemeldet.",
                }[status]}


class BrowserAutoPlugin(Plugin):
    name = "browser_auto"
    description = ("Browser selbst steuern: Seite öffnen, lesen, Links, klicken, "
                  "tippen, absenden, EINLOGGEN (Playwright; Schalter JARVIS_ALLOW_PC)")
    dangerous = True
    allow_env = ["JARVIS_ALLOW_PC", "JARVIS_ALLOW_DANGEROUS"]
    allowed_teams = ["Führung", "Automatisierung", "Web-Team", "Recherche",
                     "KI-Entwicklung", "Qualitätsmanagement", "DevOps"]

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)
        self._worker: _BrowserWorker | None = None
        self._lock = threading.Lock()
        # Zugangs-Vault liegt in DATA_DIR (~/.jarvis), also eine Ebene über 'workspace'.
        from .zugaenge import Vault
        self._vault = Vault(workspace.parent)

    def health(self) -> tuple[bool, str]:
        """Browser-Automatisierung braucht das Playwright-Paket (Browser wird lazy gestartet)."""
        import importlib.util
        if importlib.util.find_spec("playwright") is None:
            return False, "Playwright nicht installiert ('pip install playwright' + 'playwright install chromium')"
        return True, ""

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
        timeout = 120 if cmd.get("action") == "login" else 60
        try:
            status, result = resq.get(timeout=timeout)
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
        if action == "login":
            plattform = (kwargs.get("plattform") or kwargs.get("platform") or "").strip()
            if not plattform:
                raise ValueError("plattform= fehlt (z. B. plattform=instagram)")
            # "alle"/"überall" -> nacheinander in ALLE hinterlegten Konten einloggen.
            if plattform.lower() in ("alle", "all", "überall", "ueberall"):
                gespeichert = self._vault.list()
                if not gespeichert:
                    return ("[Login] Noch keine Zugänge hinterlegt. Trag deine Konten "
                            "zuerst auf der ZUGÄNGE-Seite ein.")
                ergebnisse = []
                for eintr in gespeichert:
                    r = self.run("login", plattform=eintr["plattform"])
                    ergebnisse.append({"plattform": eintr["plattform"],
                                       "ergebnis": r.get("status", r) if isinstance(r, dict) else r})
                return {"eingeloggt_bei": len(ergebnisse), "details": ergebnisse}
            eintrag = self._vault.get(plattform)
            if eintrag is None:
                return (f"[Login] Für '{plattform}' sind keine Zugangsdaten hinterlegt. "
                        f"Trag sie auf der ZUGÄNGE-Seite ein.")
            if not eintrag.get("login_url"):
                return (f"[Login] Für '{plattform}' fehlt die Login-Adresse. "
                        f"Bitte auf der ZUGÄNGE-Seite ergänzen.")
            return self._send({
                "action": "login", "plattform": plattform,
                "login_url": eintrag["login_url"],
                "user_sel": eintrag["user_sel"], "pass_sel": eintrag["pass_sel"],
                "submit_sel": eintrag["submit_sel"],
                "user": eintrag["benutzer"], "pass": eintrag["passwort"]})
        raise ValueError(f"Unbekannte Aktion: {action} "
                         "(goto|read|links|click|type|press|screenshot|login)")


def register(manager: Any, workspace: Path) -> None:
    plugin = BrowserAutoPlugin(workspace)
    manager.plugins[plugin.name] = plugin
