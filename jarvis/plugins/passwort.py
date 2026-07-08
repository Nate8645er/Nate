"""Plugin: sichere Passwörter erzeugen (lokal, mit dem secrets-Modul)."""

import secrets
import string

from jarvis.plugins.base import JarvisPlugin

# Zeichen, die man leicht verwechselt (l/1, O/0), bleiben draußen
_BUCHSTABEN = string.ascii_letters.replace("l", "").replace("O", "")
_ZIFFERN = string.digits.replace("0", "").replace("1", "")
_SONDER = "!@#$%&*+-_=?"
_ALLE = _BUCHSTABEN + _ZIFFERN + _SONDER


class PasswortPlugin(JarvisPlugin):
    name = "passwort"
    description = "Sichere Passwörter erzeugen (lokal, ohne Cloud)"
    commands = {
        "passwort": "Passwort erzeugen, z.B. /passwort oder /passwort 24",
    }

    def execute(self, command: str, args: str) -> str:
        laenge = 16
        if args.strip():
            if not args.strip().isdigit() or not 8 <= int(args) <= 64:
                return "Nutzung: /passwort <laenge> (8 bis 64 Zeichen)"
            laenge = int(args)
        while True:
            pw = "".join(secrets.choice(_ALLE) for _ in range(laenge))
            # mindestens je 1 Buchstabe, Ziffer und Sonderzeichen
            if (any(c in _BUCHSTABEN for c in pw)
                    and any(c in _ZIFFERN for c in pw)
                    and any(c in _SONDER for c in pw)):
                return (f"🔐 Dein Passwort ({laenge} Zeichen):\n  {pw}\n"
                        "(lokal erzeugt, nirgends gespeichert)")
