"""Zugänge-Vault: lokale, verschlüsselte Speicherung von Plattform-Logins.

Damit sich JARVIS auf Plattformen (E-Mail, Social, Shops …) automatisch
einloggen und dort mit deinen Daten arbeiten kann — ohne dass du jedes Mal
das Passwort tippst.

EHRLICHKEITS-PROTOKOLL
----------------------
* Alles bleibt LOKAL auf diesem PC: 0600-Datei in ~/.jarvis/zugaenge.json.
  Nichts wird an Dritte gesendet.
* Verschlüsselt mit einem lokalen Schlüssel (Fernet/AES). Optional zusätzlich
  mit einem Master-Passwort (Umgebungsvariable JARVIS_VAULT_PW):
    - OHNE Master-Passwort liegt der Schlüssel lokal (0600-Datei .vaultkey).
      Das schützt vor zufälligem Mitlesen, NICHT gegen jemanden mit vollem
      Zugriff auf deinen PC.
    - MIT Master-Passwort ist der Vault ohne dieses Passwort nicht lesbar.
* Ist das Paket 'cryptography' nicht installiert, wird als letzter Ausweg nur
  leicht verschleiert (Base64) gespeichert — dann meldet der Vault ehrlich
  `verschluesselt=False`, damit niemand sich in falscher Sicherheit wiegt.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

# Presets: bekannte Plattformen -> Login-URL + übliche Feld-Selektoren.
# So muss der Nutzer nur Benutzername + Passwort eintragen.
PRESETS: dict[str, dict[str, str]] = {
    "google": {
        "url": "https://myaccount.google.com",
        "login_url": "https://accounts.google.com/signin",
        "user_sel": "input[type=email]", "pass_sel": "input[type=password]",
        "submit_sel": "#identifierNext, #passwordNext"},
    "gmail": {
        "url": "https://mail.google.com",
        "login_url": "https://accounts.google.com/signin/v2/identifier?service=mail",
        "user_sel": "input[type=email]", "pass_sel": "input[type=password]",
        "submit_sel": "#identifierNext, #passwordNext"},
    "youtube": {
        "url": "https://www.youtube.com",
        "login_url": "https://accounts.google.com/signin",
        "user_sel": "input[type=email]", "pass_sel": "input[type=password]",
        "submit_sel": "#identifierNext, #passwordNext"},
    "instagram": {
        "url": "https://www.instagram.com",
        "login_url": "https://www.instagram.com/accounts/login/",
        "user_sel": "input[name=username]", "pass_sel": "input[name=password]",
        "submit_sel": "button[type=submit]"},
    "facebook": {
        "url": "https://www.facebook.com",
        "login_url": "https://www.facebook.com/login",
        "user_sel": "#email", "pass_sel": "#pass", "submit_sel": "button[name=login]"},
    "x": {
        "url": "https://x.com", "login_url": "https://x.com/i/flow/login",
        "user_sel": "input[autocomplete=username]",
        "pass_sel": "input[name=password]", "submit_sel": "button[data-testid=LoginForm_Login_Button]"},
    "twitter": {
        "url": "https://x.com", "login_url": "https://x.com/i/flow/login",
        "user_sel": "input[autocomplete=username]",
        "pass_sel": "input[name=password]", "submit_sel": "button[data-testid=LoginForm_Login_Button]"},
    "tiktok": {
        "url": "https://www.tiktok.com", "login_url": "https://www.tiktok.com/login",
        "user_sel": "input[name=username]", "pass_sel": "input[type=password]",
        "submit_sel": "button[type=submit]"},
    "linkedin": {
        "url": "https://www.linkedin.com", "login_url": "https://www.linkedin.com/login",
        "user_sel": "#username", "pass_sel": "#password", "submit_sel": "button[type=submit]"},
    "reddit": {
        "url": "https://www.reddit.com", "login_url": "https://www.reddit.com/login/",
        "user_sel": "input[name=username]", "pass_sel": "input[name=password]",
        "submit_sel": "button[type=submit]"},
    "github": {
        "url": "https://github.com", "login_url": "https://github.com/login",
        "user_sel": "#login_field", "pass_sel": "#password", "submit_sel": "input[type=submit]"},
    "amazon": {
        "url": "https://www.amazon.de", "login_url": "https://www.amazon.de/ap/signin",
        "user_sel": "input[type=email]", "pass_sel": "input[type=password]",
        "submit_sel": "#continue, #signInSubmit"},
    "netflix": {
        "url": "https://www.netflix.com", "login_url": "https://www.netflix.com/login",
        "user_sel": "input[name=userLoginId]", "pass_sel": "input[name=password]",
        "submit_sel": "button[type=submit]"},
    "spotify": {
        "url": "https://open.spotify.com", "login_url": "https://accounts.spotify.com/login",
        "user_sel": "#login-username", "pass_sel": "#login-password", "submit_sel": "#login-button"},
    "outlook": {
        "url": "https://outlook.live.com", "login_url": "https://login.live.com",
        "user_sel": "input[type=email]", "pass_sel": "input[type=password]",
        "submit_sel": "input[type=submit]"},
    "paypal": {
        "url": "https://www.paypal.com", "login_url": "https://www.paypal.com/signin",
        "user_sel": "#email", "pass_sel": "#password", "submit_sel": "#btnLogin"},
    "twitch": {
        "url": "https://www.twitch.tv", "login_url": "https://www.twitch.tv/login",
        "user_sel": "#login-username", "pass_sel": "#password-input",
        "submit_sel": "button[data-a-target=passport-login-button]"},
}

# Sinnvolle Standard-Selektoren, falls eine unbekannte Plattform hinzugefügt wird.
_DEFAULT_SEL = {
    "user_sel": "input[type=email], input[name=username], input[name=email], input[type=text]",
    "pass_sel": "input[type=password]",
    "submit_sel": "button[type=submit], input[type=submit]",
}


_CRYPTO_CACHE: list = []   # [Fernet|None] — einmal geprüft, dann gecacht


def _crypto():
    # BaseException (nicht nur Exception): eine kaputte/halb-installierte
    # 'cryptography' (z. B. fehlendes _cffi_backend) kann eine PanicException
    # werfen, die von 'except Exception' NICHT gefangen würde. Dann sauber auf
    # Base64-Fallback ausweichen, statt JARVIS abstürzen zu lassen. Ergebnis wird
    # gecacht, damit der (evtl. laute) Probe-Import nur EINMAL passiert.
    if _CRYPTO_CACHE:
        return _CRYPTO_CACHE[0]
    result = None
    try:
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()):
            from cryptography.fernet import Fernet  # type: ignore
            Fernet.generate_key()   # echten Funktionstest erzwingen
        result = Fernet
    except BaseException:
        result = None
    _CRYPTO_CACHE.append(result)
    return result


class Vault:
    """Verschlüsselter Zugangs-Speicher. Lädt/schreibt lazy, immer 0600."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "zugaenge.json"
        self.keyfile = data_dir / ".vaultkey"

    # --- Verschlüsselung -----------------------------------------------------
    def _fernet(self):
        try:
            return self._fernet_impl()
        except BaseException:
            return None       # kaputte crypto -> Base64-Fallback statt Absturz

    def _fernet_impl(self):
        Fernet = _crypto()
        if Fernet is None:
            return None
        pw = os.environ.get("JARVIS_VAULT_PW", "").strip()
        if pw:
            # Schlüssel aus Master-Passwort ableiten (kein Klartext gespeichert).
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            salt = b"jarvis-zugaenge-v1"
            kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=200_000)
            key = base64.urlsafe_b64encode(kdf.derive(pw.encode()))
            return Fernet(key)
        # Sonst lokalen Zufallsschlüssel verwenden/erzeugen.
        if self.keyfile.exists():
            key = self.keyfile.read_bytes()
        else:
            key = Fernet.generate_key()
            self.keyfile.write_bytes(key)
            try:
                os.chmod(self.keyfile, 0o600)
            except OSError:
                pass
        return Fernet(key)

    @property
    def verschluesselt(self) -> bool:
        return _crypto() is not None

    def _enc(self, text: str) -> str:
        f = self._fernet()
        if f is None:
            return "b64:" + base64.b64encode(text.encode()).decode()
        return "fer:" + f.encrypt(text.encode()).decode()

    def _dec(self, blob: str) -> str:
        if blob.startswith("b64:"):
            return base64.b64decode(blob[4:]).decode()
        if blob.startswith("fer:"):
            f = self._fernet()
            if f is None:
                return ""
            try:
                return f.decrypt(blob[4:].encode()).decode()
            except Exception:
                return ""      # falsches Master-Passwort o. Ä.
        return blob

    # --- Speicher ------------------------------------------------------------
    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text("utf-8"))
        except Exception:
            return {}

    def _save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    # --- öffentliche API -----------------------------------------------------
    def set(self, plattform: str, benutzer: str, passwort: str,
            login_url: str = "", url: str = "",
            user_sel: str = "", pass_sel: str = "", submit_sel: str = "") -> dict:
        key = plattform.strip().lower()
        if not key or not benutzer or not passwort:
            raise ValueError("plattform, benutzer und passwort sind nötig")
        preset = PRESETS.get(key, {})
        entry = {
            "url": url or preset.get("url", ""),
            "login_url": login_url or preset.get("login_url", url or preset.get("url", "")),
            "user_sel": user_sel or preset.get("user_sel", _DEFAULT_SEL["user_sel"]),
            "pass_sel": pass_sel or preset.get("pass_sel", _DEFAULT_SEL["pass_sel"]),
            "submit_sel": submit_sel or preset.get("submit_sel", _DEFAULT_SEL["submit_sel"]),
            "user": self._enc(benutzer),
            "pass": self._enc(passwort),
        }
        data = self._load()
        data[key] = entry
        self._save(data)
        return {"plattform": key, "gespeichert": True, "verschluesselt": self.verschluesselt}

    def get(self, plattform: str) -> dict | None:
        """Gibt den Eintrag inkl. ENTSCHLÜSSELTER Zugangsdaten zurück (nur intern)."""
        e = self._load().get(plattform.strip().lower())
        if not e:
            return None
        out = dict(e)
        out["benutzer"] = self._dec(e.get("user", ""))
        out["passwort"] = self._dec(e.get("pass", ""))
        return out

    def delete(self, plattform: str) -> bool:
        data = self._load()
        if plattform.strip().lower() in data:
            del data[plattform.strip().lower()]
            self._save(data)
            return True
        return False

    def list(self) -> list[dict]:
        """Übersicht OHNE Passwörter — nur, was gespeichert ist."""
        out = []
        for k, e in sorted(self._load().items()):
            out.append({
                "plattform": k,
                "benutzer_maskiert": _mask(self._dec(e.get("user", ""))),
                "login_url": e.get("login_url", ""),
                "hat_passwort": bool(e.get("pass")),
            })
        return out


def _mask(s: str) -> str:
    if not s:
        return "—"
    if "@" in s:
        name, _, dom = s.partition("@")
        return (name[:2] + "…") + "@" + dom
    return s[:2] + "…" if len(s) > 3 else "•••"
